# coding: utf-8

from flask import render_template, url_for
from ...utils.retail_shake_tools import dataframes as rsd
from ...utils.retail_shake_tools import maths as rsm
from ...utils.retail_shake_tools import graphs as rsg
from ..baseview import BaseView


class MonitorView(BaseView):
    def __init__(self, *args, **kwargs):
        super(MonitorView, self).__init__(*args, **kwargs)

        self.url = url_for("jobs", node=self.node, listjobs="True")
        self.spider = self.view_args["spider"]
        self.text = ""
        self.Job = None

        self.template = "scrapydweb/monitoring.html"

    def dispatch_request(self, **kwargs):
        spider_filter = f"spider = '{self.spider}'"

        df = rsd.sqlite_to_df(where=spider_filter)  # Get data
        df_tot = rsm.global_data(df)  # Compute global data
        df_tot = rsm.compute_floating_means(
            df_tot, "items"
        )  # Compute floating mean for items
        df_tot = rsm.compute_floating_means(
            df_tot, "pages"
        )  # Compute floating mean for pages
        fig = rsg.scraping_graph(dataframe=df_tot, days=90)  # Plot data
        html_fig = fig.to_html()  # Convert plot figure to html

        # fig = rsg.mini_scrap_graph(df_tot)  # Plot minimalist graph
        # html_fig = fig.to_image("svg").decode("utf-8")

        kwargs = dict(
            node=self.node,
            url=self.url,
            graphHTML=html_fig,
            spider=self.spider,
        )
        return render_template(self.template, **kwargs)
