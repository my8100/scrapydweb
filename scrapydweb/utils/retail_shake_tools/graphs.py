# -*- coding: utf-8 -*-


def scraping_graph(dataframe, days=250):
    """
    This function is used to plot the evolution of scraped items and pages with theirs respectives floating means.

    :param dataframe:   (df) spider or global DataFrame obtains from previous functions
    :param days:        (int) number of days to include into the display interval
                        (sqlite_to_df(), select_spider())
    :return:            (Graph Object.show) draw the graph object
    """
    # | import section |
    import plotly.graph_objects as go
    from datetime import timedelta, datetime

    # | variable section |
    # data = dataframe.sort_values(by="finish_date")
    data = dataframe[
        dataframe["finish_date"] > datetime.now().date() - timedelta(days=days)
    ]
    graph_name = (
        f"Evolutions du nombre d'items et de pages scrapés par jour (sur {days} j)"
    )

    # | graph section |
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["items"],
            name="Nb d'items scrapés",
            line={"color": "firebrick", "width": 3},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["items_favg"],
            name="Nb moyen d'items scrapés (7j)",
            line={
                "color": "firebrick",
                "dash": "dot",
            },
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["pages"],
            name="Nb de pages scrapées",
            line={"color": "royalblue", "width": 3},
        )
    )

    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["pages_favg"],
            name="Nb moyen de pages scrapées (7j)",
            line={"color": "royalblue", "dash": "dot"},
        )
    )

    fig.update_layout(
        title=graph_name, xaxis_title="Date", yaxis_title="Nb Items/Pages"
    )

    return fig


def mini_scrap_graph(dataframe, days=10):
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
        # dataframe["finish_date"] > datetime.now().date() - timedelta(days=days)
        dataframe["finish_date"]
        > datetime(2021, 1, 31).date() - timedelta(days=days)  # DEBUG
    ]
    data = data[data["finish_date"] < datetime(2021, 1, 31).date()]  # DEBUG

    # | graph section |
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["items"],
            name="Nb d'items scrapés",
            line={"color": "firebrick"},
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["finish_date"],
            y=data["pages"],
            name="Nb de pages scrapées",
            line={"color": "royalblue"},
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
            "showlegend": False,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "width": 250,
            "height": 200,
        }
    )

    return fig
