# coding: utf8
import os
import sys
import time
import json

import requests

CWD = os.path.dirname(os.path.abspath(__file__))
CACHE_FOLDER = os.path.join(CWD, 'cache')

scrapyd_servers, scrapydweb_host, scrapydweb_port, username, password, cache_interval_seconds = sys.argv[1:]
scrapyd_servers = json.loads(scrapyd_servers)
cache_interval_seconds = float(cache_interval_seconds)

session = requests.Session()
session.auth = (username, password)


def update_cache(state, timeout=60):
    for node, scrapyd_server in enumerate(scrapyd_servers, 1):
        try:
            r_projects = session.get('http://%s/listprojects.json' % scrapyd_server, timeout=timeout)
        except:
            continue
        projects = r_projects.json()['projects']

        for project in projects:
            r_jobs = session.get('http://%s/listjobs.json?project=%s' % (scrapyd_server, project), timeout=timeout)
            for running_job in r_jobs.json()[state]:
                try:
                    job = running_job['id']
                    spider = running_job['spider']
                    # http://127.0.0.1:5000/log/utf8/proxy/test/55f1f388a7ae11e8b9b114dda9e91c2f/
                    for opt in ['utf8', 'stats']:
                        url = ('http://{scrapydweb_host}:{scrapydweb_port}/'
                               '{node}/log/{opt}/{project}/{spider}/{job}/').format(
                            scrapydweb_host=scrapydweb_host, scrapydweb_port=scrapydweb_port,
                            node=node, opt=opt, project=project, spider=spider, job=job)
                        # 'POST' to avoid using cache, see log.py
                        session.post(url, timeout=timeout)
                        print(">>> Cache %s" % url)
                except Exception as err:
                    print(">>> Cache html fail: %s %s" % (err.__class__.__name__, err))


def main():
    while True:
        start_time = time.time()
        try:
            update_cache('running')
            update_cache('finished')
        except Exception as err:
            print(">>> Cache fail: %s %s" % (err.__class__.__name__, err))
        else:
            print(">>> Cache done at %s" % time.ctime())
        end_time = time.time()
        lasting_time = end_time - start_time
        if lasting_time < cache_interval_seconds:
            wait_time = cache_interval_seconds - lasting_time
            print(">>> Cache wait %s seconds" % int(wait_time))
            time.sleep(wait_time)


if __name__ == '__main__':
    time.sleep(10)
    main()
