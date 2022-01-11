# -*- coding: utf-8 -*-


from datetime import datetime
from typing import Sequence
from . import dataframes


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
    # | code section |

    data = dataframe[["start_date", column]].copy()

    for i in range(n -1):
        data[f"n-{i}"] = data.iloc[:, -1].shift(1)
    dataframe[f"{column}_favg"] = [row[1].mean() for row in data.iloc[:, 1:].iterrows()]

    return dataframe

def compute_floating_deviation(dataframe, column, n=3):
    """
    This function is used to compute the floating standard deviation of a specific DataFrame column at a specific interval.

    :param dataframe:   (df)    input DataFrame
    :param column:      (str)   the column name used for the mean calculation
    :param n:           (int)   the number of days to include into the mean calculation
    :return:            (df)    the input DataFrame with the floating mean column added (*_favg)
    """
    # | code section |

    data = dataframe[["start_date", column]].copy()

    for i in range(n -1):
        data[f"n-{i}"] = data.iloc[:, -1].shift(1)
    dataframe[f"{column}_fstd"] = [row[1].std() for row in data.iloc[:, 1:].iterrows()]

    return dataframe

def set_alert_level(dataframe, column, n=0, log=False):
    """
    This function is used to check if the last number of items/pages is lower than the threshold 
    
    :param dataframe:   (df)    input DataFrame
    :param column:      (str)   the column name used for the mean calculation
    :return:            (int)   the signal alert
    """
    # | import section |
    import numpy as np 
    from datetime import datetime, timedelta
    
    # | code section |
    date = datetime.now().date() - timedelta(days=n)
    if log:
        print(f"selected date:  {date}")
    data = dataframe[[f'{column}', f'{column}_favg', f'{column}_fstd']][dataframe['start_date'] == date]
    
    # Values
    try: 
      metrics = [
          0 if np.isnan(metric) else int(metric) for metric in [
              data[f'{column}'].values[0],
              data[f'{column}_favg'].values[0],
              data[f'{column}_fstd'].values[0],
          ]
      ]

      scrap_result = metrics[0]
      scrap_average = metrics[1]
      scrap_std = metrics[2]
      
    except IndexError or ValueError:
      scrap_result = 0
      scrap_average = 0
      scrap_std = 0
        
    if log:
        print(
            f"""
            Nb items:       {scrap_result}
            Avg items:      {scrap_average}
            Std items:      {scrap_std}
            Low border:     {scrap_average - scrap_std}   
            Avg items /2:   {int(np.round(scrap_average / 2))}
            """
            )

    alert_lvl = 0
    if scrap_result < np.round(scrap_average / 1.01):
        alert_lvl += 1
        if scrap_result < np.round(scrap_average - (scrap_std / 2)):
            alert_lvl += 1
            if scrap_result < np.round(scrap_average - scrap_std):
                alert_lvl += 1
                if scrap_result < np.round(scrap_average / 2) or scrap_result == 0:
                    alert_lvl += 1

    return alert_lvl

def check_alert_level(alert_levels, log=False):
    """
    This function return a HTML div with a color circle corresponding to the alert indicator
    Returns:
        * red circle if sum of alert levels > thresold
        * orange circle if sum of alert levels > thresold / 2
        * green circle if sum of alert levels < thresold / 2

    :param alert_levels:    (list)  list of alert levels 
    :param threshold:       (int)   alert threshold 
    :return:                (html)  html code of the alert indicator.
    """
    # | import section |
    import numpy as np

    # | code section |
    current_alert = np.average(alert_levels)
    
    if log:
        print(f"Sum of alert levels:   {current_alert}")
        [print(f"\t- Alert{i}: {lvl}") for i, lvl in enumerate(alert_levels)]

    if current_alert == 0:
        msg = '🟢'
    elif current_alert == 1:
        msg = '🟡'
    elif current_alert == 2:
        msg = '🟠'
    elif current_alert == 3:
        msg = '🔴'
    else:
        msg = '⚫️'

    return msg

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
