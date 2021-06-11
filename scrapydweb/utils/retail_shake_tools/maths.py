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
    sum_data = {"finish_date": [], "items": [], "pages": []}

    # | code section |
    # loop for compute the sum of scraped pages and items
    for date in dataframe.finish_date.unique():
        data = dataframe[dataframe.finish_date == date]

        sum_data["finish_date"].append(date)
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
    import numpy as np

    # | variables section |
    dataframe.reset_index(drop=True, inplace=True)

    new_column_name = column + "_favg"
    dataframe[new_column_name] = None

    # | code section |
    # loop for compute the means
    for row in dataframe.iterrows():
        # define interval limits
        low_border = row[0]
        current_index = int(low_border + n)
        # get interval data
        interval_data = dataframe.iloc[low_border:current_index]
        # save data to dataframe new column
        if current_index < dataframe.shape[0]:
            row[1][new_column_name] = np.round(interval_data[column].mean())
            dataframe.iloc[current_index] = row[1]

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
    | --- ---   | --- ---   | --- ---   |
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
