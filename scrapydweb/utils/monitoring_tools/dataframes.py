# -*- coding: utf-8 -*-
from . import maths as mtm


# TODO @h4r1c0t: multinode request
# TODO @h4r1c0t: what about mysql db server?
def sqlite_to_df(
    path=None,
    database="jobs.db",
    table="127_0_0_1_6800",  # 'all' argument to JOIN request to all the scrapyd server
    select="*",
    where="project = 'retail_shake'",
):
    """
    This function is used to automatically get data from scrapyd SQLite DB.
    By default get spyder data from 127.0.0.1:6800 table of the jobs.db

    :param path:    (str) path to the *.db file (default: local pathway to jobs.db)
    :param database: (str) the database to select
    :param table:   (str) table name (default: 127.0.0.1:6800, the default server)
    :param select:  (str) column to select (default: * all the columns)
    :param where:   (str) where condition for the select  (default: spider from 'retail_shake' project)
    :return:        (df)  query output as a pandas DataFrame
    """
    # | import section |
    import sqlite3
    import pandas as pd

    # | code section |
    # db connect
    if not path:
        from scrapydweb_settings_v10 import DATABASE_URL

        path = DATABASE_URL + "/" + database
        path = path.replace("sqlite:///", "")  # !!! > mysql / postgre options
    con = sqlite3.connect(path)

    # import data
    df = pd.read_sql(
        f"""
        SELECT {select}
        FROM '{table}'
        WHERE {where}
        """,
        con,
    )

    # create date format and sort
    df.start = pd.to_datetime(df.start)
    df["start_date"] = df.start.dt.date
    df = df.sort_values(by="start_date")

    df["items"] = df["items"].fillna(0)
    df["pages"] = df["pages"].fillna(0)

    return df


def select_spider(dataframe, spider_name):
    """
    This function is used to extract a specific spider from the DataFrame obtains with sqlite_to_df() function.

    :param dataframe:       (df)  the DataFrame obtains with sqlite_to_df() function
    :param spider_name:     (str) the spider name to extract
    :return:                (df)  a DataFrame with the data corresponding to the spider selected
                            and means items and pages
    """
    # | code section |
    # get specific column of the dataframe for the specific spider name
    data = dataframe[["spider", "start_date", "items", "pages"]][
        dataframe["spider"] == spider_name
    ]
    # TODO : See witch *'fill method'* is the best for dates
    data = data.fillna(method="ffill").sort_values(by="start_date")

    # automatically compute the floating means
    data = mtm.compute_floating_means(data, "items", 7)
    data = mtm.compute_floating_means(data, "pages", 7)

    return data
