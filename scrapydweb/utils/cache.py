# coding: utf8
import os
import sys
import platform
import time
import re
import json

import requests
try:
    from psutil import pid_exists
except ImportError:
    PSUTIL_AVAILABLE = False
else:
    PSUTIL_AVAILABLE = True


verbose = True
IN_WINDOWS = True if platform.system() == 'Windows' else False
pattern_jobs = re.compile(r"""<tr>
                        <td>(?P<Project>.*?)</td>
                        <td>(?P<Spider>.*?)</td>
                        <td>(?P<Job>.*?)</td>
                        (?:<td>(?P<PID>.*?)</td>)?
                        (?:<td>(?P<Start>.*?)</td>)?
                        (?:<td>(?P<Runtime>.*?)</td>)?
                        (?:<td>(?P<Finish>.*?)</td>)?
                        (?:<td>(?P<Log>.*?)</td>)?
                        (?:<td>(?P<Items>.*?)</td>)?
                        </tr>
                    """, re.X)
keys_jobs = ['project', 'spider', 'job', 'pid', 'start', 'runtime', 'finish', 'log', 'items']


def printf(value, warn=False):
    if not verbose and not warn:
        return
    prefix = "!!! " if warn else ""
    print("%sHTML caching %s" % (prefix, value))


# https://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid-in-python
def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


class RefreshCache(object):

    def __init__(self, scrapydweb_bind, scrapydweb_port,
                 node, SCRAPYD_SERVER, auth,
                 session, timeout, cache_request_interval,
                 ignore_finished_bool_list, finished_jobs_dict):
        self.scrapydweb_bind = scrapydweb_bind
        self.scrapydweb_port = scrapydweb_port
        self.node = node
        self.SCRAPYD_SERVER = SCRAPYD_SERVER
        self.auth = tuple(auth) if auth else auth  # TypeError: 'list' object is not callable
        self.session = session
        self.timeout = timeout
        self.cache_request_interval = cache_request_interval
        self.ignore_finished_bool_list = ignore_finished_bool_list
        self.finished_jobs_dict = finished_jobs_dict

        self.url_jobs = 'http://%s/jobs' % self.SCRAPYD_SERVER
        self.running_jobs = []
        self.finished_jobs_set = set()
        self.finished_jobs = []

        self.url_stats = ('http://{scrapydweb_bind}:{scrapydweb_port}/'
                          '{node}/log/{opt}/{project}/{spider}/{job}/?job_finished={job_finished}')

    def main(self):
        self.fetch_jobs()

        for job_tuple in self.running_jobs + self.finished_jobs:
            self.fetch_stats(job_tuple)

    def fetch_jobs(self):
        try:
            r = self.session.get(self.url_jobs, auth=self.auth, timeout=self.timeout)
            assert r.status_code == 200, "got status_code: %s" % r.status_code
        except Exception as err:
            # import traceback
            # print(traceback.format_exc())
            printf("request jobs failed: %s" % err, warn=True)
        else:
            printf("request jobs got (%s) %s bytes: %s" % (r.status_code, len(r.content), self.url_jobs))
            rows = [dict(zip(keys_jobs, row)) for row in pattern_jobs.findall(r.text)]
            for row in rows:
                job_tuple = (row['project'], row['spider'], row['job'])
                if row['pid']:
                    self.running_jobs.append(job_tuple)
                elif row['finish']:
                    self.finished_jobs_set.add(job_tuple)

            self.update_finished_jobs()
        finally:
            time.sleep(self.cache_request_interval)

    def update_finished_jobs(self):
        finished_jobs_set_previous = self.finished_jobs_dict.setdefault(self.node, set())
        # set([2,3]).difference(set([1,2])) => {3}
        finished_jobs_set_new_added = self.finished_jobs_set.difference(finished_jobs_set_previous)
        self.finished_jobs_dict[self.node] = self.finished_jobs_set
        # print(len(self.finished_jobs_dict[self.node]))

        ignore = self.ignore_finished_bool_list[self.node-1]
        for job_tuple in finished_jobs_set_new_added:
            if ignore:
                printf('ignore finished job from node %s: %s' % (self.node, job_tuple))
            else:
                self.finished_jobs.append(job_tuple)
        if ignore:
            self.ignore_finished_bool_list[self.node-1] = False

    def fetch_stats(self, job_tuple):
        (project, spider, job) = job_tuple
        job_finished = True if job_tuple in self.finished_jobs else ''
        kwargs = dict(
            scrapydweb_bind=self.scrapydweb_bind,
            scrapydweb_port=self.scrapydweb_port,
            node=self.node,
            opt='stats',
            project=project,
            spider=spider,
            job=job,
            job_finished=job_finished
        )
        # http://127.0.0.1:5000/log/utf8/proxy/test/55f1f388a7ae11e8b9b114dda9e91c2f/
        url = self.url_stats.format(**kwargs)
        try:
            # Make POST request to avoid using cached HTML, see log.py
            r = session.post(url, timeout=self.timeout)
            assert r.status_code == 200, "got status_code %s" % r.status_code
        except Exception as err:
            printf("request stats page failed: %s" % err, warn=True)
            if job_finished:
                self.finished_jobs_dict[self.node].remove(job_tuple)
        else:
            printf("request stats page got (%s) %s bytes: %s" % (r.status_code, len(r.content), url))
        finally:
            time.sleep(self.cache_request_interval)


def main():
    while True:
        if (PSUTIL_AVAILABLE and not pid_exists(main_pid)) or (not IN_WINDOWS and not check_pid(main_pid)):
            sys.exit("!!! Caching subprocess %s exit: main_pid %s NOT exists" % (caching_pid, main_pid))
        start_time = time.time()
        try:
            for node, SCRAPYD_SERVER in enumerate(SCRAPYD_SERVERS, 1):
                updater = RefreshCache(scrapydweb_bind, scrapydweb_port,
                                       node, SCRAPYD_SERVER, SCRAPYD_SERVERS_AUTHS[node-1],
                                       session, timeout, cache_request_interval,
                                       ignore_finished_bool_list, finished_jobs_dict)
                updater.main()

            printf("done at %s" % time.ctime())
            printf("cost %s seconds" % int(time.time() - start_time))
            printf("sleep %s seconds" % cache_round_interval)
            time.sleep(cache_round_interval)
        except KeyboardInterrupt:
            sys.exit("!!! Caching subprocess %s cancelled by KeyboardInterrupt" % caching_pid)
        except Exception as err:
            printf("error: %s" % err, warn=True)


if __name__ == '__main__':
    (main_pid,
     scrapydweb_bind, scrapydweb_port, username, password,
     SCRAPYD_SERVERS, SCRAPYD_SERVERS_AUTHS,
     cache_round_interval, cache_request_interval,
     verbose) = sys.argv[1:]

    main_pid = int(main_pid)
    SCRAPYD_SERVERS = json.loads(SCRAPYD_SERVERS)
    SCRAPYD_SERVERS_AUTHS = json.loads(SCRAPYD_SERVERS_AUTHS)
    cache_round_interval = int(cache_round_interval)
    cache_request_interval = int(cache_request_interval)
    verbose = True if verbose == 'True' else False

    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
    session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000))
    if username and password:
        session.auth = (username, password)
    timeout = 60

    caching_pid = os.getpid()
    ignore_finished_bool_list = [True] * len(SCRAPYD_SERVERS)
    finished_jobs_dict = {}

    main()
