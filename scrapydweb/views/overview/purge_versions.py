# coding: utf-8
from collections import defaultdict
from distutils.version import LooseVersion

import requests
from flask import jsonify

from ...common import handle_metadata, session
from ..baseview import BaseView


metadata = dict(pageview=handle_metadata().get('pageview', 1))


class PurgeVersionsView(BaseView):
    metadata = metadata

    def __init__(self):
        super().__init__()

    def dispatch_request(self, **kwargs):
        max_version = LooseVersion(kwargs['version'])
        to_delete = {}

        for server in self.SCRAPYD_SERVER_OBJECTS:
            url = server.url() + f'/listversions.json?project={kwargs["project"]}'
            versions = []
            try:
                versions = session.get(url, auth=server.auth).json()['versions']
            except requests.exceptions.ConnectionError: pass
            to_delete[server] = [ver for ver in versions if LooseVersion(ver) < max_version]
            if len(versions) > 0 and len(to_delete[server]) == len(versions):
                return f"This would delete all versions on {server.name}! Refusing to do that.", 406

        count = 0
        if self.POST:
            deleted = defaultdict(dict)
            for server, versions in to_delete.items():
                for version in versions:
                    count += 1
                    deleted[server.name][version] = session.post(server.url() + f'/delversion.json', auth=server.auth, data={
                        "project": kwargs["project"],
                        "version": version
                    }).json()
            # return jsonify(deleted)
            return f"Deleted {count} versions across {len(to_delete)} nodes"

        else:
            return jsonify({server.name: versions for server, versions in to_delete.items()})
