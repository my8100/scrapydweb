# -*- coding: utf-8 -*-

from . import maths as mtm


def mysql_connector(
    url=None,
    database="scrapydweb_jobs",
):
    """
    This function is used to get a connector to the scrapyd MySQL DB.
    By default, connected to the scrapydweb_jobs database.

    :param url:
    :param database: (str) the database to select
    :return:         (sqlite3.con) the db connector
    """
    # | import section |
    import re
    import mysql.connector
    from mysql.connector import connect, errorcode
    from ...vars import DATABASE_URL

    # | code section |
    # db connect
    con = None

    if not url:
        user, password = re.findall(r"(?<=//)(.*?)(?=@)", DATABASE_URL)[0].split(":")
        host, port = re.findall(r"(?<=@)(.*?)$", DATABASE_URL)[0].split(":")
    else:
        user, password = re.findall(r"(?<=//)(.*?)(?=@)", url)[0].split(":")
        host, port = re.findall(r"(?<=@)(.*?)$", url)[0].split(":")

    try:
        con = connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            auth_plugin="mysql_native_password",
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print("Oops, something goes wrong:\n\t", err)

    return con


def sqlite_connector(
    path=None,
    database="jobs.db",
):
    """
    This function is used to get a connector to the scrapyd SQLite DB.
    By default, connected to the jobs.db.

    :param path:     (str) path to the *.db file (default: local pathway to jobs.db)
    :param database: (str) the database to select
    :return:         (sqlite3.con) the db connector
    """
    # | import section |
    import sqlite3

    # | code section |
    # db connect
    if not path:
        from scrapydweb_settings_v10 import DATABASE_URL

        path = DATABASE_URL + "/" + database
        path = path.replace("sqlite:///", "")  # !!! > mysql / postgre options

    con = sqlite3.connect(path)

    return con


# TODO #2 @h4r1c0t: multinode request -> get the current node and the corresponding server.
def sql_to_df(con, select="*", table="127_0_0_1_6800", where="project = retail_shake"):
    """
    This function is used to automatically get data from scrapyd DB as a Pandas dataframe.

    :param con:     (sql connector) the connector for the scrapydweb DB
    :param table:   (str) table name (default: 127_0_0_1_6800, local server as default)
    :param select:  (str) column to select (default: * all the columns)
    :param where:   (str) where condition for the select  (default: spider from 'retail_shake' project)
    :return:        (df)  query output as a pandas DataFrame
    """
    # | import section |
    import pandas as pd

    # | code section |
    # import data
    df = pd.read_sql(
        f"""
        SELECT {select}
        FROM {table}
        WHERE {where};
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
