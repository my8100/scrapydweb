# coding: utf8
import json
from pprint import pprint

import requests
from flask import current_app as app

session = requests.Session()


def make_request(url, data=None, timeout=60, api=True, log=True, auth=None):
    """
    :param api: return dict if set True, else text
    """
    try:
        if log:
            if 'addversion.json' in url and data:
                app.logger.debug('>>>>> %s %s %s' % ('POST' if data else 'GET', url,
                                                     {'project': data.get('project'), 'version': data.get('project'),
                                                      'egg': "%s bytes binary egg file" % len(data.get('egg'))}))
            else:
                app.logger.debug('>>>>> %s %s %s' % ('POST' if data else 'GET', url, data or ''))
                if data:
                    pprint(data)
        if data:
            r = session.post(url, data=data, timeout=timeout, auth=auth)
        else:
            r = session.get(url, timeout=timeout, auth=auth)
        r.encoding = 'utf8'
    except Exception as err:
        if log:
            app.logger.error('!!!!! %s %s' % (err.__class__.__name__, err))
        if api:
            return -1, {'url': url, 'auth': auth, 'status_code': -1,
                        'status': 'error', 'message': str(err)}
        else:
            return -1, str(err)
    else:
        if api:
            try:
                r_json = r.json()
            except json.JSONDecodeError: # When Scrapyd server reboot, listprojects got 502 html
                r_json = {'status': 'error', 'message': r.text}
            finally:
                if log:
                    sign = '!!!!! ' if (r.status_code != 200 or r_json.get('status') != 'ok') else '<<<<< '
                    app.logger.debug('%s%s %s' % (sign, r.status_code, r_json))
                r_json.update(dict(url=url, auth=auth, status_code=r.status_code))

                return r.status_code, r_json
        else:
            if r.status_code == 200:
                front = r.text[:min(100, len(r.text))].replace('\n', '')
                back = r.text[-min(100, len(r.text)):].replace('\n', '')
                if log:
                    app.logger.debug('<<<<< %s %s\n...%s' % (r.status_code, front, back))
            else:
                if log:
                    app.logger.debug('!!!!! %s %s' % (r.status_code, r.text))

            return r.status_code, r.text


def json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)
