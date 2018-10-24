# coding: utf8
import re

from flask import Blueprint, render_template, url_for, request
from flask import current_app as app

from ..vars import DEFAULT_LATEST_VERSION, pattern_directory, keys_directory
from ..utils import make_request

bp = Blueprint('items', __name__, url_prefix='/')


# https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_filters.html#other-useful-filters
# https://stackoverflow.com/questions/12791216/how-do-i-use-regular-expressions-in-jinja2
# https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask
@bp.app_template_filter()
def regex_replace(s, find, replace):
    return re.sub(find, replace, s)


@bp.route('/<int:node>/items/<project>/<spider>/')
@bp.route('/<int:node>/items/<project>/')
@bp.route('/<int:node>/items/')
def items(node, project=None, spider=None):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE = 'scrapydweb/simpleui/items.html' if SIMPLEUI else 'scrapydweb/items.html'
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]
    SCRAPYD_SERVERS_AUTHS = app.config.get('SCRAPYD_SERVERS_AUTHS', [None])

    url = 'http://{}/items/{}{}'.format(SCRAPYD_SERVER,
                                       '%s/' % project if project else '',
                                       '%s/' % spider if spider else '')
    auth = SCRAPYD_SERVERS_AUTHS[node - 1]
    url_auth = url.replace('http://', 'http://%s:%s@' % auth) if auth else url
    status_code, text = make_request(url, api=False, auth=auth)

    if status_code != 200 or not re.search(r'Directory', text):
        return render_template(TEMPLATE_RESULT, node=node,
                               url=url_auth, status_code=status_code, text=text,
                               message='Check out https://scrapyd.readthedocs.io/en/latest/config.html#items-dir for help')

    rows = [dict(zip(keys_directory, row)) for row in pattern_directory.findall(text)]

    for row in rows:
        # <a href="demo/">demo/</a>
        # <a href="test/">test/</a>
        # <a href="2018-10-09_225255.jl">2018-10-09_225255.jl</a>
        if project and spider:
            m = re.search(r'>(.*?)<', row['filename'])
            filename = m.group(1)
            # UnicodeEncodeError: 'ascii' codec can't encode characters in position 58-59: ordinal not in range(128)
            row['filename'] = u'<a class="link" target="_blank" href="{}">{}</a>'.format(
                               url_auth + filename, filename)
        else:
            if SIMPLEUI:
                row['filename'] = re.sub(r'href="(.*?)"', r'href="\1?ui=simple"', row['filename'])
            else:
                row['filename'] = re.sub(r'href=', 'class="link" href=', row['filename'])

    return render_template(TEMPLATE, node=node,
                           project=project, spider=spider, rows=rows, url=url_auth)
