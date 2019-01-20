# coding: utf8
from flask import redirect, url_for

from .myview import MyView


class IndexView(MyView):

    def __init__(self):
        super(self.__class__, self).__init__()

    def dispatch_request(self, **kwargs):
        if self.SCRAPYD_SERVERS_AMOUNT == 1:
            if self.IS_MOBILE and not self.IS_IPAD:
                return redirect(url_for('dashboard', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('dashboard', node=self.node, ui=self.UI))
        else:
            if self.USE_MOBILEUI or (self.IS_MOBILE and not self.IS_IPAD):
                return redirect(url_for('dashboard', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('overview', node=self.node, ui=self.UI))
