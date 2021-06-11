# coding: utf-8
import re

from flask import render_template, url_for
from ...utils.retail_shake_tools import dataframes as rsd
from ...utils.retail_shake_tools import maths as rsm
from ...utils.retail_shake_tools import graphs as rsg
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

        df = rsd.sqlite_to_df(where="spider = 'castorama_pagelist'")  # Get data
        df_tot = rsm.global_data(df)  # Compute global data
        df_tot = rsm.compute_floating_means(
            df_tot, "items"
        )  # Compute floating mean for items
        df_tot = rsm.compute_floating_means(
            df_tot, "pages"
        )  # Compute floating mean for pages
        # fig = rsg.scraping_graph(df_tot)  # Plot data
        # html_fig = fig.to_html()  # Convert plot figure to html

        fig = rsg.mini_scrap_graph(df_tot)  # Plot minimalist graph
        html_fig = fig.to_image("svg").decode("utf-8")

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
