# -*- coding: utf-8 -*-
from ...vars import DATABASE_URL
import pandas as pd

from ...utils.monitoring_tools import dataframes as mtd
from ..baseview import BaseView


class ThumbnailView(BaseView):
    def __init__(self, *args, **kwargs):
        super(ThumbnailView, self).__init__(*args, **kwargs)

        self.spider = self.view_args["spider"]

    def dispatch_request(self, **kwargs):
        df = None
        con, db_type = mtd.db_connect(DATABASE_URL, return_db_type=True)

        table = self.SCRAPYD_SERVER.replace(".", "_").replace(":", "_")

        if db_type == "sqlite":
            df = mtd.jobs_df_format(
                pd.read_sql(
                    f"""
                    SELECT * 
                    FROM '{table}'
                    WHERE spider = {self.spider} AND julianday('now') - julianday(start) <= 14
                    """,
                    con=con,
                )
            )
        elif db_type == "mysql":
            df = mtd.jobs_df_format(
                pd.read_sql(
                    f"""
                    SELECT *
                    FROM {table}
                    WHERE spider = "{self.spider}" AND DATEDIFF(NOW(), start) <= 14
                    """,
                    con=con,
                )
            )

        if df is not None:
            df = mtd.select_last_date(df, "start_date")
            return df.to_json(orient="records")
