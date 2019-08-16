# coding: utf-8
import json
import logging
import os
import platform
import re
import sys
import time
import traceback

try:
    from psutil import pid_exists
except ImportError:
    pid_exists = None

import requests
from requests.adapters import HTTPAdapter


logger = logging.getLogger('scrapydweb.utils.poll')  # __name__
_handler = logging.StreamHandler()
_formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s in %(name)s: %(message)s")
_handler.setFormatter(_formatter)
logger.addHandler(_handler)

IN_WINDOWS = platform.system() == 'Windows'
JOB_PATTERN = re.compile(r"""
                            <tr>
                                <td>(?P<Project>.*?)</td>
                                <td>(?P<Spider>.*?)</td>
                                <td>(?P<Job>.*?)</td>
                                (?:<td>(?P<PID>.*?)</td>)?
                                (?:<td>(?P<Start>.*?)</td>)?
                                (?:<td>(?P<Runtime>.*?)</td>)?
                                (?:<td>(?P<Finish>.*?)</td>)?
                                (?:<td>(?P<Log>.*?)</td>)?
                                (?:<td>(?P<Items>.*?)</td>)?
                                [\w\W]*?  # Temp support for Scrapyd v1.3.0 (not released)
                            </tr>
                          """, re.X)
JOB_KEYS = ['project', 'spider', 'job', 'pid', 'start', 'runtime', 'finish', 'log', 'items']


class Poll(object):
    logger = logger

    def __init__(self, url_scrapydweb, username, password,
                 scrapyd_servers, scrapyd_servers_auths,
                 poll_round_interval, poll_request_interval,
                 main_pid, verbose, exit_timeout=0):
        self.url_scrapydweb = url_scrapydweb
        self.auth = (username, password) if username and password else None

        self.scrapyd_servers = scrapyd_servers
        self.scrapyd_servers_auths = scrapyd_servers_auths

        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
        self.session.mount('https://', HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
        # if username and password:
            # self.session.auth = (username, password)
        self.timeout = 60

        self.poll_round_interval = poll_round_interval
        self.poll_request_interval = poll_request_interval

        self.ignore_finished_bool_list = [True] * len(self.scrapyd_servers)
        self.finished_jobs_dict = {}

        self.main_pid = main_pid
        self.poll_pid = os.getpid()

        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.exit_timeout = exit_timeout

        self.init_time = time.time()
        self.url_stats = self.url_scrapydweb + '/{node}/log/{opt}/{project}/{spider}/{job}/?job_finished={job_finished}'

    def check_exit(self):
        exit_condition_1 = pid_exists is not None and not pid_exists(self.main_pid)
        exit_condition_2 = not IN_WINDOWS and not self.check_pid(self.main_pid)
        if exit_condition_1 or exit_condition_2:
            sys.exit("!!! Poll subprocess (pid: %s) exits "
                     "since main_pid %s not exists" % (self.poll_pid, self.main_pid))

    # https://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid-in-python
    @staticmethod
    def check_pid(pid):
        """ Check For the existence of a unix pid. """
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    def fetch_jobs(self, node, url, auth):
        running_jobs = []
        finished_jobs_set = set()
        self.logger.debug("[node %s] fetch_jobs: %s", node, url)
        r = self.make_request(url, auth=auth, post=False)
        # Should not invoke update_finished_jobs() if fail to fetch jobs
        assert r is not None, "[node %s] fetch_jobs failed: %s" % (node, url)

        self.logger.debug("[node %s] fetch_jobs got (%s) %s bytes", node, r.status_code, len(r.content))
        # Temp support for Scrapyd v1.3.0 (not released)
        text = re.sub(r'<thead>.*?</thead>', '', r.text, flags=re.S)
        jobs = [dict(zip(JOB_KEYS, job)) for job in re.findall(JOB_PATTERN, text)]
        for job in jobs:
            job_tuple = (job['project'], job['spider'], job['job'])
            if job['pid']:
                running_jobs.append(job_tuple)
            elif job['finish']:
                finished_jobs_set.add(job_tuple)
        self.logger.debug("[node %s] got running_jobs: %s", node, len(running_jobs))
        self.logger.debug("[node %s] got finished_jobs_set: %s", node, len(finished_jobs_set))
        return running_jobs, finished_jobs_set

    def fetch_stats(self, node, job_tuple, finished_jobs):
        (project, spider, job) = job_tuple
        job_finished = 'True' if job_tuple in finished_jobs else ''
        kwargs = dict(
            node=node,
            opt='stats',
            project=project,
            spider=spider,
            job=job,
            job_finished=job_finished
        )
        # http://127.0.0.1:5000/log/stats/proxy/test/55f1f388a7ae11e8b9b114dda9e91c2f/
        url = self.url_stats.format(**kwargs)
        self.logger.debug("[node %s] fetch_stats: %s", node, url)
        # Make POST request to trigger alert, see log.py
        r = self.make_request(url, auth=self.auth, post=True)
        if r is None:
            self.logger.error("[node %s %s] fetch_stats failed: %s", node, self.scrapyd_servers[node-1], url)
            if job_finished:
                self.finished_jobs_dict[node].remove(job_tuple)
                self.logger.info("[node %s] retry in next round: %s", node, url)
        else:
            self.logger.debug("[node %s] fetch_stats got (%s) %s bytes from %s",
                              node, r.status_code, len(r.content), url)

    def main(self):
        while True:
            self.check_exit()
            start_time = time.time()
            try:
                self.run()
                end_time = time.time()
                self.logger.debug("Took %.1f seconds", (end_time - start_time))
                if 0 < self.exit_timeout < end_time - self.init_time:
                    self.logger.critical("GoodBye, exit_timeout: %s", self.exit_timeout)
                    break
                else:
                    self.logger.info("Sleeping for %ss", self.poll_round_interval)
                    time.sleep(self.poll_round_interval)
            except KeyboardInterrupt:
                self.logger.warning("Poll subprocess (pid: %s) cancelled by KeyboardInterrupt", self.poll_pid)
                sys.exit()
            except Exception:
                self.logger.error(traceback.format_exc())

    def make_request(self, url, auth, post=False):
        try:
            if post:
                r = self.session.post(url, auth=auth, timeout=self.timeout)
            else:
                r = self.session.get(url, auth=auth, timeout=self.timeout)
            r.encoding = 'utf-8'
            assert r.status_code == 200, "got status_code %s" % r.status_code
        except Exception as err:
            self.logger.error("make_request failed: %s\n%s", url, err)
            return None
        else:
            return r

    def run(self):
        for node, (scrapyd_server, auth) in enumerate(zip(self.scrapyd_servers, self.scrapyd_servers_auths), 1):
            # Update Jobs history
            # url_jobs = self.url_scrapydweb + '/%s/jobs/' % node
            # self.make_request(url_jobs, auth=self.auth, post=True)

            url_jobs = 'http://%s/jobs' % scrapyd_server
            # json.loads(json.dumps({'auth':(1,2)})) => {'auth': [1, 2]}
            auth = tuple(auth) if auth else None  # TypeError: 'list' object is not callable
            try:
                running_jobs, finished_jobs_set = self.fetch_jobs(node, url_jobs, auth)
                finished_jobs = self.update_finished_jobs(node, finished_jobs_set)
                for job_tuple in running_jobs + finished_jobs:
                    self.fetch_stats(node, job_tuple, finished_jobs)
                    self.logger.debug("Sleeping for %ss", self.poll_request_interval)
                    time.sleep(self.poll_request_interval)
            except KeyboardInterrupt:
                raise
            except AssertionError as err:
                self.logger.error(err)
            except Exception:
                self.logger.error(traceback.format_exc())

    def update_finished_jobs(self, node, finished_jobs_set):
        finished_jobs_set_previous = self.finished_jobs_dict.setdefault(node, set())
        self.logger.debug("[node %s] previous finished_jobs_set: %s", node, len(finished_jobs_set_previous))
        # set([2,3]).difference(set([1,2])) => {3}
        finished_jobs_set_new_added = finished_jobs_set.difference(finished_jobs_set_previous)
        self.finished_jobs_dict[node] = finished_jobs_set
        self.logger.debug("[node %s] now finished_jobs_set: %s", node, len(self.finished_jobs_dict[node]))
        if finished_jobs_set_new_added:
            self.logger.info("[node %s] new added finished_jobs_set: %s", node, finished_jobs_set_new_added)
        else:
            self.logger.debug("[node %s] new added finished_jobs_set: %s", node, finished_jobs_set_new_added)

        finished_jobs = []
        ignore = self.ignore_finished_bool_list[node-1]
        for job_tuple in finished_jobs_set_new_added:
            if ignore:
                self.logger.debug("[node %s] ignore finished job: %s", node, job_tuple)
            else:
                finished_jobs.append(job_tuple)
        if ignore:
            self.ignore_finished_bool_list[node-1] = False
            self.logger.debug("[node %s] new added finished_jobs after filter: %s", node, len(finished_jobs))
        return finished_jobs


def main(args):
    keys = ('url_scrapydweb', 'username', 'password',
            'scrapyd_servers', 'scrapyd_servers_auths',
            'poll_round_interval', 'poll_request_interval',
            'main_pid', 'verbose', 'exit_timeout')
    kwargs = dict(zip(keys, args))
    kwargs['scrapyd_servers'] = json.loads(kwargs['scrapyd_servers'])
    kwargs['scrapyd_servers_auths'] = json.loads(kwargs['scrapyd_servers_auths'])
    kwargs['poll_round_interval'] = int(kwargs['poll_round_interval'])
    kwargs['poll_request_interval'] = int(kwargs['poll_request_interval'])
    kwargs['main_pid'] = int(kwargs['main_pid'])
    kwargs['verbose'] = kwargs['verbose'] == 'True'
    kwargs['exit_timeout'] = int(kwargs.setdefault('exit_timeout', 0))  # For test only

    poll = Poll(**kwargs)
    poll.main()
    return poll.ignore_finished_bool_list  # For test only


if __name__ == '__main__':
    main(sys.argv[1:])
