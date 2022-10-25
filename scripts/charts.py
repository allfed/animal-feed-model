import pathlib
import plotly.express as px
import pandas as pd
from difflib import diff_bytes
import numpy as np
from dash import Dash, dcc, html, Output, Input, dash_table  # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components
import re
from io import StringIO
from dateutil.relativedelta import relativedelta
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


def percentage_change(col1, col2):
    return ((col2 - col1) / col1) * 100


def slaughter_week_creator():
    PATH = pathlib.Path(__file__).parent
    DATA_PATH = PATH.joinpath("../data").resolve()
    df = pd.read_csv(DATA_PATH.joinpath("usda/run_results_2020_slaughter.csv"))

    d = []  # create empty list to place variables in to in loop
    weeks = 53
    offset = 12

    for i in range(weeks):

        single_file = df.iloc[i + offset, 3]
        StringData = StringIO(single_file)
        df3 = pd.read_csv(StringIO(single_file), sep="\t", header=None)

        date_line = df3.iloc[3, 0]
        date_line_list = re.split("\s+", date_line)
        data_date = date_line_list[2]

        cattle_line = df3.iloc[22, 0]
        cattle_line_list = re.split("\s+", cattle_line)
        data_cattle = cattle_line_list[2]

        hogs_line = df3.iloc[42, 0]
        hogsline_list = re.split("\s+", hogs_line)
        data_hogs = hogsline_list[2]

        d.append({"Date": data_date, "Cattle": data_cattle, "Hogs": data_hogs})

    df_final = pd.DataFrame(d)

    df_final.to_csv("slaughter_2020.csv")

    return df


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
df = pd.read_csv(
    DATA_PATH.joinpath("usda_other_data/double_year_percentChange.csv"),
    index_col="Date",
)
df.index = pd.to_datetime(df.index)

# graph_colours = ["#75787B", "#3A913F", "#DC582A", "#674230", "#3A913F", "#75787B"]

# df


# df2 = df.resample('D').mean()
# df.resample('D').interpolate()[::7]


fig, ax = plt.subplots(constrained_layout=True)
locator = mdates.MonthLocator()
formatter = mdates.ConciseDateFormatter(locator)
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
plt.plot(df["PercentChange"] * 0)
plt.plot(df["PercentChange"])
# plt.plot(df["Cattle"])
# plt.plot(df["Cattle.1"])
plt.title("Percent Change in Weekly Slaughter 2019-2020")
plt.xlabel("Week of Slaughter")
plt.ylabel("Percentage Change")
ax.xaxis.label.set_color("dimgrey")
ax.yaxis.label.set_color("dimgrey")
plt.show()


# fig = px.line(
#     df, x="Date", y="Cattle", color="Year", color_discrete_sequence=graph_colours
# )

# fig.show()
