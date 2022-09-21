import pathlib
import plotly.express as px
import pandas as pd
from difflib import diff_bytes
import numpy as np
from dash import Dash, dcc, html, Output, Input, dash_table # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components

"""
Start main function
"""   
# find dataframe
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
df = pd.read_csv(DATA_PATH.joinpath('NassCattle2022.csv'), index_col="Variable")
df["Qty"] = df["Qty"].astype("float")

# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server # for heroku deployment

mytitle = dcc.Markdown(children="")
mysubtitle = dcc.Markdown(children="")
scatter = dcc.Graph(figure={})
bar = dcc.Graph(figure={})

### Create slider components on a card
controls = dbc.Card(
    [
        dbc.Label(
            "Change the interventions to see effect on cow population"
        ),
        html.Div(
            [
                dbc.Label("Decrease Beef Birth Rate"),
                dcc.Slider(
                    0,
                    100,
                    value=100,
                    id="myslider1",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Decrease Dairy Birth Rate"),
                dcc.Slider(
                    0,
                    100,
                    value=20,
                    id="myslider2",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Increase Slaughter Rate"),
                dcc.Slider(
                    0,
                    600,
                    value=100,
                    id="myslider3",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Months"),
                dcc.Slider(
                    0,
                    24,
                    value=12,
                    step=1,
                    id="myslider4",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
    ],
    body=True,
)


# Customize your own Layout
app.layout = dbc.Container(
    [
        dbc.Row([dbc.Col([mytitle], width=6)], justify="center"),
        dbc.Row([dbc.Col([mysubtitle], width=6)], justify="center"),
        dbc.Row(
            [
                dbc.Col(controls, md=3),
                dbc.Col([scatter], width=9),
            ],
            align="center",
        ),
        html.Hr(),
    
    dbc.Row([dbc.Col([bar], width=12)], justify="center"),        
    ],
    fluid=True,
)

# Callback allows components to interact
@app.callback(
    Output(scatter, "figure"),
    Output(bar, "figure"),
    Output(mytitle, "children"),
    Output(mysubtitle, "children"),
    Input("myslider1", "value"),
    Input("myslider2", "value"),
    Input("myslider3", "value"),
    Input("myslider4", "value")
)
def update_graph(
    reduction_in_beef_calves, reduction_in_dairy_calves, increase_in_slaughter, months
):  # function arguments come from the component property of the Input

    # other baseline variables
    slaughtering_pm = 2900
    feed_percentage = 100
    dairy_life_expectancy = 5

    # define vairbales from data 
    starting_herd_size = df.loc["Cattle and calves", "Qty"]
    total_calves = df.loc["Calves under 500 pounds", "Qty"]
    dairy_cows = df.loc["Milk cows", "Qty"]
    beef_cows = df.loc["Beef cows", "Qty"]
    beef_steers = df.loc["Steers 500 pounds and over", "Qty"]
    heifers = df.loc["Heifers 500 pounds and over", "Qty"]
    bulls = df.loc["Bulls 500 pounds and over", "Qty"]
    new_calves_per_year = df.loc["Calf crop", "Qty"]
    cattle_on_feed = df.loc["Cattle on feed", "Qty"]

    # calaculate number of cows
    dairy_beef_mother_ratio = dairy_cows / beef_cows
    dairy_heifers = heifers * dairy_beef_mother_ratio
    beef_heifers = heifers - dairy_heifers

    dairy_calves = dairy_beef_mother_ratio * total_calves
    beef_calves = total_calves - dairy_calves
    dairy_calf_steers = dairy_calves / 2
    dairy_calf_girls = dairy_calves / 2

    calves_destined_for_beef_ratio = (beef_calves + dairy_calf_steers) / total_calves
    new_beef_calfs = calves_destined_for_beef_ratio * new_calves_per_year
    new_dairy_calfs =   new_calves_per_year - new_beef_calfs

    cattle_in_beef_track = (
        dairy_calf_steers + beef_calves + beef_steers + beef_cows + beef_heifers
    )
    cattle_in_dairy_rack = dairy_calf_girls + dairy_cows + dairy_heifers



    # interventions
    reduction_in_beef_calves *= 0.01
    reduction_in_dairy_calves *= 0.01
    increase_in_slaughter *= 0.01


    ## define current totals
    current_beef_feed_cattle = cattle_on_feed
    current_beef_cattle = cattle_in_beef_track
    current_dairy_cattle = cattle_in_dairy_rack
    current_total_cattle = cattle_in_dairy_rack+cattle_in_beef_track
    current_slaughter_rate = slaughtering_pm*increase_in_slaughter

    # per month
    other_death_rate = 0.005 # 
    new_beef_calfs_pm = (new_beef_calfs / 12)*(1-reduction_in_beef_calves)
    new_dairy_calfs_pm = (new_dairy_calfs / 12)*(1-reduction_in_dairy_calves)



    d = [] # temp list

    for i in range(months):
        other_beef_death = other_death_rate*current_beef_cattle
        other_dairy_death = other_death_rate*current_dairy_cattle

        current_beef_cattle -= other_beef_death
        current_dairy_cattle -= other_dairy_death

        dairy_slaughter = current_dairy_cattle/(dairy_life_expectancy*12)
        beef_slaughter = current_slaughter_rate-dairy_slaughter

        current_beef_cattle += (new_beef_calfs_pm - beef_slaughter)
        current_dairy_cattle += (new_dairy_calfs_pm - dairy_slaughter)

        if current_beef_cattle < 0:
            current_beef_cattle = 0
        if current_dairy_cattle < 0:
            current_dairy_cattle = 0

        current_total_cattle = +current_beef_cattle+current_dairy_cattle

        d.append(
            {
                'Total Pop': current_total_cattle,
                'Beef Pop': current_beef_cattle,
                'Dairy Pop':  current_dairy_cattle,
                'Month': i 
            })

    df_final = pd.DataFrame(d)

    # https://plotly.com/python/scatterpleth-maps/
    fig1 = px.scatter(df_final, x="Month", y="Total Pop", range_y=[30000,100000])

    # fig2 = px.bar(df_final, x="Month", y="Total Pop")
    fig2 = px.bar(df_final, x="Month", y=["Beef Pop", "Dairy Pop"], title="Population Make-up")
    return (
        fig1,
        fig2,
        "# " "Cow Population",
        "Modelled beef and dairy industry",
    )  # returned objects are assigned to the component property of the Output

# Run app
if __name__ == "__main__":
    app.run_server(debug=False, port=8055)

