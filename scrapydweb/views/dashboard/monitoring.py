# coding: utf-8
from os.path import dirname
from flask import render_template, url_for
from ...utils.monitoring_tools import dataframes as mtd
from ...utils.monitoring_tools import maths as mtm
from ...utils.monitoring_tools import graphs as mtg
from ..baseview import BaseView


class MonitorView(BaseView):
    def __init__(self, *args, **kwargs):
        super(MonitorView, self).__init__(*args, **kwargs)

        self.url = url_for("jobs", node=self.node, listjobs="True")
        self.spider = self.view_args["spider"]
        self.text = ""
        self.Job = None

        self.log_url = None
        self.image_path = (
            dirname(dirname(dirname(__file__))) + "/static/images/thumbnails/"
        )
        self.template = "scrapydweb/monitoring.html"

    def dispatch_request(self, **kwargs):
        spider_filter = f"spider = '{self.spider}'"

        df = mtd.sqlite_to_df(where=spider_filter)  # Get data
        df = mtm.compute_floating_means(df, "items")  # Compute floating mean for items
        df = mtm.compute_floating_means(df, "pages")  # Compute floating mean for pages
        fig = mtg.scraping_graph(dataframe=df, days=30)  # Plot data
        html_fig = fig.to_html()  # Convert plot figure to html

        # fig = mtg.mini_scrap_graph(df)  # Plot minimalist graph
        # fig.write_image(self.image_path + self.spider + ".png")

        last_job = df[df["start"] == df["start"].max()]
        self.log_url = (
            "http://127.0.0.1:5000/"
            + str(self.node)
            + "/log/utf8/"
            + str(last_job.project.values[0])
            + "/"
            + str(last_job.spider.values[0])
            + "/"
            + str(last_job.job.values[0])
            + "/?job_finished=True"
        )
        print("\n\n##########\n", self.log_url, "\n##########\n\n")
        # png_fig = fig.to_image("png")
        github_link = self.github_issue_generator()

        kwargs = dict(
            node=self.node,
            url=self.url,
            graphHTML=html_fig,
            spider=self.spider,
            github_link=github_link,
            log_url=self.log_url,
        )
        return render_template(self.template, **kwargs)

    def github_issue_generator(self):
        from urllib import parse

        github_repo_url = "https://github.com/Retail-Shake/scraping/issues/new"
        title = f"[BUG] '{self.spider}' - "
        body = parse.quote(
            f"""
### Describe the defect
There is a problem on '{self.spider} with ...

### Comments
*your comments here ...*
### Logs
[log link here]({self.log_url})          
### Picture    
![image](/static/images/monitor/{self.spider}.png)       
"""
        )
        label = "bug"
        link = f"body={body}&title={title}&labels={label}"
        link = github_repo_url + "?" + link

        return link
