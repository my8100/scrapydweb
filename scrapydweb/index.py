# coding: utf8
from flask import url_for, redirect

from .myview import MyView


class IndexView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

    def dispatch_request(self, **kwargs):
        if len(self.SCRAPYD_SERVERS) == 1:
            if self.IS_MOBILE and not self.IS_IPAD:
                return redirect(url_for('dashboard', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('dashboard', node=self.node, ui=self.UI))
        else:
            if self.IS_MOBILEUI or (self.IS_MOBILE and not self.IS_IPAD):
                return redirect(url_for('dashboard', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('overview', node=self.node, ui=self.UI))
