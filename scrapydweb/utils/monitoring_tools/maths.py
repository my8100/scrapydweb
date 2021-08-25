# -*- coding: utf-8 -*-


def global_data(dataframe):
    """
    This function can be used to compute the total of pages and items scraped each day.

    :param dataframe:   (df) input DataFrame with 'pages' and 'items' columns to compute the sum.
    :return:            (df) output global DataFrame this the sum of 'items' and 'pages' for each date.
    """
    # | import section |
    import pandas as pd

    # | variable section |
    sum_data = {"start_date": [], "items": [], "pages": []}

    # | code section |
    # loop for compute the sum of scraped pages and items
    for date in dataframe.start_date.unique():
        data = dataframe[dataframe.start_date == date]

        sum_data["start_date"].append(date)
        sum_data["items"].append(data["items"].sum())
        sum_data["pages"].append(data["pages"].sum())

    return pd.DataFrame(sum_data)


def compute_floating_means(dataframe, column, n=3):
    """
    This function is used to compute the floating mean of a specific DataFrame column at a specific interval.

    :param dataframe:   (df)    input DataFrame
    :param column:      (str)   the column name used for the mean calculation
    :param n:           (int)   the number of days to include into the mean calculation
    :return:            (df)    the input DataFrame with the floating mean column added (*_favg)
    """
    # | import section |
    import pandas as pd
    import numpy as np

    # | code section |

    data = dataframe[["start_date", column]].copy()

    for i in range(n -1):
        data[f"n-{i}"] = data.iloc[:, -1].shift(1)
    dataframe[f"{column}_favg"] = [row[1].mean() for row in data.iloc[:, 1:].iterrows()]

    return dataframe


def unique_count(dataframe, column):
    """
    This function return a dict with unique entry of a dataframe column as key and the total of iteration for this
    entry as value.

    *e.g.,*

    >>> import pandas as pd
    >>> df = pd.DataFrame({'col1': ['A', 'B', 'A', 'A', 'B', 'A'], 'col2': [1, 2, 1, 4, 3, 3]})
    >>> df
    ```
    |       | col1  | col2  |
    |  ---  |  ---  |  ---  |
    | 0     | A     | 1     |
    | 1     | B     | 2     |
    | 2     | A     | 1     |
    | 3     | A     | 4     |
    | 4     | B     | 3     |
    | 5     | A     | 3     |
    ```
    >>> unique_count(df, 'col1')
    >>> {'A': 4, 'B':2}
    >>> unique_count(df, 'col2')
    >>> {'1': 2, '2': 1, '3': 2, '4': 1}

    :param dataframe:   (df)    input DataFrame
    :param column:      (str)   column name
    :return:            (dict)  count dict
    """
    return {
        col: dataframe[column][dataframe[column] == col].count()
        for col in dataframe[column].unique()
    }
