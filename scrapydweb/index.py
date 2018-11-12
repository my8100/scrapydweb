# coding: utf8
from flask import url_for, redirect

from .myview import MyView


class IndexView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

    def dispatch_request(self, **kwargs):
        if self.IS_SIMPLEUI or len(self.SCRAPYD_SERVERS) == 1:
            return redirect(url_for('dashboard', node=self.node, ui=self.UI))
        else:
            return redirect(url_for('overview', node=self.node))
