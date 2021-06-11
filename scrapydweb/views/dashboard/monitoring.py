# coding: utf-8
import re

from flask import render_template, url_for
from ...utils.retail_shake_tools import dataframes as rsdf
from ...utils.retail_shake_tools import maths as rscalc
from ...utils.retail_shake_tools import graphs as rsgrph
from ..baseview import BaseView


class MonitorView(BaseView):
    def __init__(self, *args, **kwargs):
        super(MonitorView, self).__init__(*args, **kwargs)

        self.url = url_for("jobs", node=self.node, listjobs="True")
        self.text = ""
        self.Job = None
        # self.pending_jobs = []
        # self.running_jobs = []
        # self.finished_jobs = []
        self.template = "scrapydweb/monitoring.html"

    def dispatch_request(self, **kwargs):

        df = rsdf.sqlite_to_df(where="spider = 'castorama_pagelist'")
        df_tot = rscalc.global_data(df)
        df_tot = rscalc.compute_floating_means(df_tot, "items")
        df_tot = rscalc.compute_floating_means(df_tot, "pages")
        fig = rsgrph.scraping_graph(df_tot)
        # graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        html_fig = fig.to_html()

        kwargs = dict(
            node=self.node,
            url=self.url,
            # pending_jobs=self.pending_jobs,
            # running_jobs=self.running_jobs,
            # finished_jobs=self.finished_jobs,
            url_report=url_for(
                "log",
                node=self.node,
                opt="report",
                project="PROJECT_PLACEHOLDER",
                spider="SPIDER_PLACEHOLDER",
                job="JOB_PLACEHOLDER",
            ),
            url_schedule=url_for("schedule", node=self.node),
        )
        return render_template(self.template, **kwargs, graphHTML=html_fig)
