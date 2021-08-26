# -*- coding: utf-8 -*-

import re
import logging
from sqlite3 import OperationalError
from . import maths as mtm


def db_connect(database_url, return_db_type=False):
    """
    This function is used to select automatically the correct SQL connector from the DATABASE_URL
    :param database_url:    (str) DATABASE_URL provided into the scrapydweb settings
    :param return_db_type:  (bool) if True, it will return a str with the type of db detected. It could be used to
                            select the query syntax.
    :return:                (connector) sql connector for request the DB
    """
    if re.findall(r"sqlite", database_url):
        try:
            con = sqlite_connector()
            db_type = "sqlite"
            logging.info("Connected to SQLite DB!")
            if return_db_type:
                return con, db_type
            else:
                return con
        except OperationalError as err:
            logging.error("SQLite DB connection failed!\n\t", err)
    elif re.findall("mysql", database_url):
        try:
            con = mysql_connector(url=database_url)
            db_type = "mysql"
            logging.info("Connected to tht MySQL server!")
            if return_db_type:
                return con, db_type
            else:
                return con
        except ConnectionError or AttributeError as err:
            logging.error("MySQL server connection failed!\n\t", err)
    else:
        logging.error("Connection type not handled yet...")


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
        from ...vars import DATABASE_URL

        path = DATABASE_URL + "/" + database
        path = path.replace("sqlite:///", "")
    con = sqlite3.connect(path)

    return con


def jobs_df_format(dataframe):
    """
    This function is used to automatically format jobs query result to a time series pandas dataframe

    :dataframe:     (df)  input jobs dataframe
    :return:        (df)  output formated pandas DataFrame
    """
    # | import section |
    import pandas as pd

    # | code section |
    # create date format and sort
    dataframe.start = pd.to_datetime(dataframe.start)
    dataframe["start_date"] = dataframe.start.dt.date
    df = dataframe.sort_values(by="start_date")

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


def select_last_date(dataframe, date_column):
    index = list(
        {
            date: j
            for j, date in zip(
                range(len(dataframe)),
                [dataframe.iloc[i, :][date_column] for i in range(len(dataframe))],
            )
        }.values()
    )
    return dataframe.iloc[index, :]
