# coding: utf8
import re

from flask import Blueprint, render_template, url_for, request
from flask import current_app as app

from ..vars import DEFAULT_LATEST_VERSION, pattern_directory, keys_directory
from ..utils import make_request

bp = Blueprint('directory', __name__, url_prefix='/')


# https://ansible-docs.readthedocs.io/zh/stable-2.0/rst/playbooks_filters.html#other-useful-filters
# https://stackoverflow.com/questions/12791216/how-do-i-use-regular-expressions-in-jinja2
# https://www.michaelcho.me/article/custom-jinja-template-filters-in-flask
@bp.app_template_filter()
def regex_replace(s, find, replace):
    return re.sub(find, replace, s)


@bp.route('/<int:node>/directory/<project>/<spider>/')
@bp.route('/<int:node>/directory/<project>/')
@bp.route('/<int:node>/directory/')
def directory(node, project=None, spider=None):
    SIMPLEUI = True if request.args.get('ui', '') == 'simple' else False
    UI = 'simple' if SIMPLEUI else None
    TEMPLATE = 'scrapydweb/simpleui/directory.html' if SIMPLEUI else 'scrapydweb/directory.html'
    TEMPLATE_RESULT = 'scrapydweb/simpleui/result.html' if SIMPLEUI else 'scrapydweb/result.html'

    SCRAPYD_SERVERS = app.config.get('SCRAPYD_SERVERS', ['127.0.0.1:6800'])
    SCRAPYD_SERVER = SCRAPYD_SERVERS[node - 1]

    url = 'http://{}/logs/{}{}'.format(SCRAPYD_SERVER,
                                       '%s/' % project if project else '',
                                       '%s/' % spider if spider else '')
    status_code, text = make_request(url, api=False)

    if status_code != 200 or not re.search(r'Directory', text):
        return render_template(TEMPLATE_RESULT, node=node,
                               url=url, status_code=status_code, text=text)

    rows = [dict(zip(keys_directory, row)) for row in pattern_directory.findall(text)]

    for row in rows:
        if project and spider:
            # <a href="098726cca42b11e8a8b514dda9e91c2f.log">098726cca42b11e8a8b514dda9e91c2f.log</a>
            m = re.search(r'>(.*?)<', row['filename'])
            filename = m.group(1)
            row['filename'] = filename
            job = filename.rpartition('.')[0] or filename

            row['url_logs_utf8'] = url_for('logs.logs', node=node, opt='utf8', project=project, spider=spider, job=job,
                                           ui=UI)
            row['url_logs_stats'] = url_for('logs.logs', node=node, opt='stats', project=project, spider=spider,
                                            job=job, ui=UI)
            if SIMPLEUI:
                row['url_start'] = url_for('api.api', node=node, opt='start', project=project,
                                           version_spider_job=spider, ui=UI)
            else:
                row['url_start'] = url_for('schedule.schedule', node=node, project=project,
                                           version=DEFAULT_LATEST_VERSION, spider=spider)
                row['url_multinode_start'] = url_for('overview.overview', node=node, opt='schedule', project=project,
                                                     version_job=DEFAULT_LATEST_VERSION, spider=spider)
        else:
            # <a href="proxy/">proxy/</a>
            if SIMPLEUI:
                row['filename'] = re.sub(r'href="(.*?)"', r'href="\1?ui=simple"', row['filename'])
            else:
                row['filename'] = re.sub(r'href=', 'class="link" href=', row['filename'])

    return render_template(TEMPLATE, node=node,
                           project=project, spider=spider, rows=rows, url=url)
