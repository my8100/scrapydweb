#!/usr/bin/python2
# coding=utf-8

import glob
import json
import netrc
import os
import shutil
import sys
import tempfile
import time
from optparse import OptionParser
from subprocess import Popen, PIPE, check_call

import setuptools  # not used in code but needed in runtime, don't remove!
from scrapy.utils.conf import get_config, closest_scrapy_cfg
from scrapy.utils.http import basic_auth_header
from scrapy.utils.project import inside_project
from scrapy.utils.python import retry_on_eintr
from six.moves.urllib.error import HTTPError, URLError
from six.moves.urllib.parse import urlparse, urljoin
from six.moves.urllib.request import (build_opener, install_opener,
                                      HTTPRedirectHandler as UrllibHTTPRedirectHandler,
                                      Request, urlopen)
from w3lib.form import encode_multipart

_SETUP_PY_TEMPLATE = \
"""# Automatically created by: scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name         = 'project',
    version      = '1.0',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = %(settings)s']},
)
"""

def parse_opts():
    parser = OptionParser(usage="%prog [options] [ [target] | -l | -L <target> ]",
        description="Deploy Scrapy project to Scrapyd server")
    parser.add_option("-p", "--project",
        help="the project name in the target")
    parser.add_option("-v", "--version",
        help="the version to deploy. Defaults to current timestamp")
    parser.add_option("-l", "--list-targets", action="store_true", \
        help="list available targets")
    parser.add_option("-a", "--deploy-all-targets",action="store_true", help="deploy all targets")
    parser.add_option("-d", "--debug", action="store_true",
        help="debug mode (do not remove build dir)")
    parser.add_option("-L", "--list-projects", metavar="TARGET", \
        help="list available projects on TARGET")
    parser.add_option("--egg", metavar="FILE",
        help="use the given egg, instead of building it")
    parser.add_option("--build-egg", metavar="FILE",
        help="only build the egg, don't deploy it")
    return parser.parse_args()

def main():
    opts, args = parse_opts()
    exitcode = 0
    if not inside_project():
        _log("Error: no Scrapy project found in this location")
        sys.exit(1)

    install_opener(
        build_opener(HTTPRedirectHandler)
    )

    if opts.list_targets:
        for name, target in _get_targets().items():
            print("%-20s %s" % (name, target['url']))
        return

    if opts.list_projects:
        target = _get_target(opts.list_projects)
        req = Request(_url(target, 'listprojects.json'))
        _add_auth_header(req, target)
        f = urlopen(req)
        projects = json.loads(f.read())['projects']
        print(os.linesep.join(projects))
        return

    tmpdir = None

    if opts.build_egg: # build egg only
        egg, tmpdir = _build_egg()
        _log("Writing egg to %s" % opts.build_egg)
        shutil.copyfile(egg, opts.build_egg)
    elif opts.deploy_all_targets:
        version = None
        for name, target in _get_targets().items():
            if version is None:
                version = _get_version(target, opts)
            _build_egg_and_deploy_target(target, version, opts)
    else: # buld egg and deploy
        target_name = _get_target_name(args)
        target = _get_target(target_name)
        version = _get_version(target, opts)
        exitcode, tmpdir = _build_egg_and_deploy_target(target, version, opts)

    if tmpdir:
        if opts.debug:
            _log("Output dir not removed: %s" % tmpdir)
        else:
            shutil.rmtree(tmpdir)

    sys.exit(exitcode)

def _build_egg_and_deploy_target(target, version, opts):
    exitcode = 0
    tmpdir = None

    project = _get_project(target, opts)
    if opts.egg:
        _log("Using egg: %s" % opts.egg)
        egg = opts.egg
    else:
        _log("Packing version %s" % version)
        egg, tmpdir = _build_egg()
    if not _upload_egg(target, egg, project, version):
        exitcode = 1
    return exitcode, tmpdir

def _log(message):
    sys.stderr.write(message + os.linesep)

def _fail(message, code=1):
    _log(message)
    sys.exit(code)

def _get_target_name(args):
    if len(args) > 1:
        raise _fail("Error: Too many arguments: %s" % ' '.join(args))
    elif args:
        return args[0]
    elif len(args) < 1:
        return 'default'

def _get_project(target, opts):
    project = opts.project or target.get('project')
    if not project:
        raise _fail("Error: Missing project")
    return project

def _get_option(section, option, default=None):
    cfg = get_config()
    return cfg.get(section, option) if cfg.has_option(section, option) \
        else default

def _get_targets():
    cfg = get_config()
    baset = dict(cfg.items('deploy')) if cfg.has_section('deploy') else {}
    targets = {}
    if 'url' in baset:
        targets['default'] = baset
    for x in cfg.sections():
        if x.startswith('deploy:'):
            t = baset.copy()
            t.update(cfg.items(x))
            targets[x[7:]] = t
    return targets

def _get_target(name):
    try:
        return _get_targets()[name]
    except KeyError:
        raise _fail("Unknown target: %s" % name)

def _url(target, action):
    return urljoin(target['url'], action)

def _get_version(target, opts):
    version = opts.version or target.get('version')
    if version == 'HG':
        p = Popen(['hg', 'tip', '--template', '{rev}'], stdout=PIPE, universal_newlines=True)
        d = 'r%s' % p.communicate()[0]
        p = Popen(['hg', 'branch'], stdout=PIPE, universal_newlines=True)
        b = p.communicate()[0].strip('\n')
        return '%s-%s' % (d, b)
    elif version == 'GIT':
        p = Popen(['git', 'describe'], stdout=PIPE, universal_newlines=True)
        d = p.communicate()[0].strip('\n')
        if p.wait() != 0:
            p = Popen(['git', 'rev-list', '--count', 'HEAD'], stdout=PIPE, universal_newlines=True)
            d = 'r%s' % p.communicate()[0].strip('\n')

        p = Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=PIPE, universal_newlines=True)
        b = p.communicate()[0].strip('\n')
        return '%s-%s' % (d, b)
    elif version:
        return version
    else:
        # 这里要转成分钟级别的，防止不同机器版本号不一样
        return str(int(time.time()) / 60 * 60) + "_" + time.strftime("%Y-%m-%dT%H:%M:00", time.localtime())
        # return str(int(time.time()))

def _upload_egg(target, eggpath, project, version):
    with open(eggpath, 'rb') as f:
        eggdata = f.read()
    data = {
        'project': project,
        'version': version,
        'egg': ('project.egg', eggdata),
    }
    body, boundary = encode_multipart(data)
    url = _url(target, 'addversion.json')
    headers = {
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
        'Content-Length': str(len(body)),
    }
    req = Request(url, body, headers)
    _add_auth_header(req, target)
    _log('Deploying to project "%s" in %s' % (project, url))
    return _http_post(req)

def _add_auth_header(request, target):
    if 'username' in target:
        u, p = target.get('username'), target.get('password', '')
        request.add_header('Authorization', basic_auth_header(u, p))
    else: # try netrc
        try:
            host = urlparse(target['url']).hostname
            a = netrc.netrc().authenticators(host)
            request.add_header('Authorization', basic_auth_header(a[0], a[2]))
        except (netrc.NetrcParseError, IOError, TypeError):
            pass

def _http_post(request):
    try:
        f = urlopen(request)
        _log("Server response (%s):" % f.code)
        print(f.read().decode('utf-8'))
        return True
    except HTTPError as e:
        _log("Deploy failed (%s):" % e.code)
        resp = e.read().decode('utf-8')
        try:
            d = json.loads(resp)
        except ValueError:
            print(resp)
        else:
            if "status" in d and "message" in d:
                print("Status: %(status)s" % d)
                print("Message:\n%(message)s" % d)
            else:
                print(json.dumps(d, indent=3))
    except URLError as e:
        _log("Deploy failed: %s" % e)

def _build_egg():
    closest = closest_scrapy_cfg()
    os.chdir(os.path.dirname(closest))
    if not os.path.exists('setup.py'):
        settings = get_config().get('settings', 'default')
        _create_default_setup_py(settings=settings)
    d = tempfile.mkdtemp(prefix="scrapydeploy-")
    o = open(os.path.join(d, "stdout"), "wb")
    e = open(os.path.join(d, "stderr"), "wb")
    retry_on_eintr(check_call, [sys.executable, 'setup.py', 'clean', '-a', 'bdist_egg', '-d', d], stdout=o, stderr=e)
    o.close()
    e.close()
    egg = glob.glob(os.path.join(d, '*.egg'))[0]
    return egg, d

def _create_default_setup_py(**kwargs):
    with open('setup.py', 'w') as f:
        f.write(_SETUP_PY_TEMPLATE % kwargs)


class HTTPRedirectHandler(UrllibHTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newurl = newurl.replace(' ', '%20')
        if code in (301, 307):
            return Request(newurl,
                                   data=req.get_data(),
                                   headers=req.headers,
                                   origin_req_host=req.get_origin_req_host(),
                                   unverifiable=True)
        elif code in (302, 303):
            newheaders = dict((k, v) for k, v in req.headers.items()
                              if k.lower() not in ("content-length", "content-type"))
            return Request(newurl,
                                   headers=newheaders,
                                   origin_req_host=req.get_origin_req_host(),
                                   unverifiable=True)
        else:
            raise HTTPError(req.get_full_url(), code, msg, headers, fp)


if __name__ == "__main__":
    main()
