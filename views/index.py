# coding: utf-8
from flask import redirect, url_for

from .baseview import BaseView


class IndexView(BaseView):

    def __init__(self):
        super(IndexView, self).__init__()

    def dispatch_request(self, **kwargs):
        if self.SCRAPYD_SERVERS_AMOUNT == 1:
            if self.IS_MOBILE and not self.IS_IPAD:
                return redirect(url_for('jobs', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('jobs', node=self.node, ui=self.UI))
        else:
            if self.USE_MOBILEUI or (self.IS_MOBILE and not self.IS_IPAD):
                return redirect(url_for('jobs', node=self.node, ui='mobile'))
            else:
                return redirect(url_for('servers', node=self.node, ui=self.UI))
