# -*- coding: utf-8 -*-


def scraping_graph(dataframe, days=90, n=7):
    """
    This function is used to plot the evolution of scraped items and pages with theirs respectives floating means.

    :param dataframe:   (df) spider or global DataFrame obtains from previous functions
    :param days:        (int) number of days to include into the display interval
                        (sql_to_df(), select_spider())
    :param n:           (int) number of days taken for the floating mean calculation
    :return:            (Graph Object) plot build json
    """
    # | import section |
    import plotly.graph_objects as go
    from datetime import timedelta, datetime

    # | variable section |
    data = dataframe[
        dataframe["start_date"] >= datetime.now().date() - timedelta(days=days)
    ]
    data = data.sort_values(by="start_date")

    graph_name = (
        f"Evolution of scraped items and pages scraped each day (on {days} days)"
    )
    
    data['low_border'] = data["items_favg"] - data["items_fstd"]
    data['low_border'] = data['low_border'].apply(lambda x: 0 if x < 0 else x)

    # | graph section |
    fig = go.Figure()

    # --- Number of items scrapped
    # #-- add number of items scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["items"],
            name="Number scraped items",
            line={"color": "firebrick", "width": 4},
            hovertemplate='Nb Items: %{y}<extra></extra>',
            marker={"opacity": 0}
        )
    )

    # #-- add lower border of variations for number of items scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data['low_border'],
            name="",
            line={
                "color": "firebrick",
                "width": 0
            },
            showlegend=False,
            hoverinfo='skip',
            marker={"opacity": 0}
        )
    )

    # #-- add average number of items scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["items_favg"],
            name=f"Average scraped items ({n}d)",
            fill='tonexty',
            line={"color": "firebrick", "dash": "dot"},
            hoverinfo='skip',
            marker={"opacity": 0}
        )
    )

    # --- Number of pages scrapped
    # #-- add number of pages scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["pages"],
            # yaxis="y2",
            name="Number scraped pages",
            # line={"color": "royalblue", "width": 3},
            line={"color": "#555555", "width": 3},
            hovertemplate='Nb Pages: %{y}<extra></extra>',
            marker={"opacity": 0}
        )
    )

    # #-- add lower border of variations for number of pages scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data['low_border'],
            # yaxis="y2",
            name="",
            # line={"color": "royalblue", "dash": "dot"},
            line={"color": "#555555", "width": 0},
            showlegend=False,
            hoverinfo='skip',
            marker={"opacity": 0}
        )
    )

    # #-- add average number of pages scrapped
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["pages_favg"],
            # yaxis="y2",
            name="",
            fill='tonexty',
            # line={"color": "royalblue", "dash": "dot"},
            line={"color": "#555555", "dash": "dot"},
            hoverinfo='skip',
            marker={"opacity": 0}
        )
    )

    fig.update_layout(
        title=graph_name,
        xaxis_title="Date",
        yaxis_title="Nb Items / Pages",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(rangemode="tozero")

    return fig


def mini_scrap_graph(dataframe, days=7):
    """
    This function is used to plot the evolution of scraped items and pages with theirs respectives floating means.

    :param dataframe:   (df) spider or global DataFrame obtains from previous functions
                        (sqlite_to_df(), select_spider())
    :param days:        (int) number of days to include into the display interval
    :return:            (Graph Object.show) draw the graph object
    """
    # | import section |
    import plotly.graph_objects as go
    import numpy as np
    from datetime import timedelta, datetime

    # | variable section |
    # data = dataframe.sort_values(by="finish_date")
    data = dataframe[
        dataframe["start_date"]
        > datetime.now().date() - timedelta(days=days)
        # dataframe["start_date"]
        # > datetime(2021, 1, 31).date() - timedelta(days=days)  # DEBUG
    ]
    # data = data[data["start_date"] < datetime(2021, 1, 31).date()]  # DEBUG

    # | graph section |
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["items"],
            name="Nb d'items scrapés",
            line={"color": "firebrick"},
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["start_date"],
            y=data["pages"],
            yaxis="y2",
            name="Nb de pages scrapées",
            line={"color": "#555555"},
            mode="lines",
        )
    )
    # update y axes
    y_min = np.min(np.array(data["pages"]))
    y_max = np.max(np.array(data["items"]))
    fig.update_yaxes(range=[y_min, y_max])

    # update fig layout to remove axis and background
    fig.update_layout(
        {
            "xaxis": {
                "showgrid": False,
                "zeroline": False,
                "visible": False,
            },
            "yaxis": {
                "showgrid": False,
                "zeroline": False,
                "visible": False,
            },
            "yaxis2": {
                "showgrid": False,
                "zeroline": False,
                "visible": False,
            },
            "showlegend": False,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "width": 300,
            "height": 200,
        }
    )

    return fig
