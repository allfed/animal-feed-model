import pathlib
import plotly.express as px
import pandas as pd
from difflib import diff_bytes
import numpy as np
from dash import Dash, dcc, html, Output, Input, dash_table  # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components


PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
df = pd.read_fwf(DATA_PATH.joinpath("SJ_LS71320191227.TXT"))






