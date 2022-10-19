import pathlib
import plotly.express as px
import pandas as pd
from difflib import diff_bytes
import numpy as np
from dash import Dash, dcc, html, Output, Input, dash_table  # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components

"""
Start main function
"""
# Create dataframes
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
df = pd.read_csv(DATA_PATH.joinpath("NassCattle2022.csv"), index_col="Variable")
df2 = pd.read_csv(DATA_PATH.joinpath("NassPigs2022.csv"), index_col="Variable")
df["Qty"] = df["Qty"].astype("float")

#### Do Dash things below, skip ahead to callback function for the main event
# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server  # for heroku deployment

mytitle = dcc.Markdown(children="")
# mysubtitle = dcc.Markdown(children="")
scatter = dcc.Graph(figure={})
scatter2 = dcc.Graph(figure={})
bar = dcc.Graph(figure={})
bar2 = dcc.Graph(figure={})
bar3 = dcc.Graph(figure={})
bar4 = dcc.Graph(figure={})

### Create slider components on a card
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Baseline Slaughter Rate"),
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
                dbc.Label(
                    "Proportion of Slaughter which is mothers"
                ),  # (proxy for termination of pregnancies too, but not the same as a percentage)
                dcc.Slider(
                    0,
                    100,
                    value=0,
                    id="myslider8",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label(
                    "Discount Rate for Labour/Technology Transfer between species"
                ),
                dcc.Slider(
                    0,
                    100,
                    value=50,
                    id="myslider7",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Decrease Beef Birth Rate"),
                dcc.Slider(
                    0,
                    100,
                    value=00,
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
                    value=0,
                    id="myslider2",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Reduction Pig Breeding"),
                dcc.Slider(
                    0,
                    100,
                    value=0,
                    id="myslider4",
                    updatemode="drag",
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Reduction Poultry Breeding"),
                dcc.Slider(
                    0,
                    100,
                    value=0,
                    id="myslider5",
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
                    id="myslider6",
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
        # dbc.Row([dbc.Col([mysubtitle], width=6)], justify="center"),
        dbc.Row(
            [
                dbc.Col(controls, md=3),
                dbc.Col([bar], width=9),
            ],
            align="center",
        ),
        html.Hr(),
        dbc.Row([dbc.Col([bar2], width=12)], justify="center"),
        dbc.Row([dbc.Col([bar3], width=12)], justify="center"),
        dbc.Row([dbc.Col([bar4], width=12)], justify="center"),
        dbc.Row([dbc.Col([scatter], width=12)], justify="center"),
        dbc.Row([dbc.Col([scatter2], width=12)], justify="center"),
    ],
    fluid=True,
)


#### Callback function here, this is where it all happens
# Callback allows components to interact
@app.callback(
    Output(scatter, "figure"),
    Output(bar, "figure"),
    Output(bar2, "figure"),
    Output(bar3, "figure"),
    Output(bar4, "figure"),
    Output(scatter2, "figure"),
    Output(mytitle, "children"),
    # Output(mysubtitle, "children"),
    Input("myslider1", "value"),
    Input("myslider2", "value"),
    Input("myslider3", "value"),
    Input("myslider4", "value"),
    Input("myslider5", "value"),
    Input("myslider6", "value"),
    Input("myslider7", "value"),
    Input("myslider8", "value"),
)
def update_graph(
    reduction_in_beef_calves,
    reduction_in_dairy_calves,
    increase_in_slaughter,
    reduction_in_pig_breeding,
    reduction_in_poultry_breeding,
    months,
    discount_rate,
    mother_slaughter,
):  # function arguments come from the component property of the Input (in this case, the sliders)

    poultry_visual_optimiser = 1
    magnitude_adjust = 1000
    feed_unit_adjust = 0.0005  # convert pounds to tons
    ## unpack all the dataframe information for ease of use ##
    # pigs
    total_pigs = df2.loc["TotalPigs", "Qty"]
    piglets_pm = df2.loc["PigletsPerMonth", "Qty"]
    pigs_slaughter_pm = df2.loc["SlaughterPerMonth", "Qty"]
    pigGestation = df2.loc["pigGestation", "Qty"]
    piglets_per_litter = 7.5

    # poultry
    total_poultry = (
        2127170289 / 1000
    )  # USDA everything is in 1000 head, so divide this number by 1000
    poultry_slaughter_pm = 853670.0  # USDA
    chicks_pm = poultry_slaughter_pm  # assume the same, no data
    poultryGestation = 1  # actaully 21 days, let's round to 1 month

    # cows (more complex, as need to split dairy and beef)
    total_calves = df.loc["Calves under 500 pounds", "Qty"]
    dairy_cows = df.loc["Milk cows", "Qty"]
    beef_cows = df.loc["Beef cows", "Qty"]
    beef_steers = df.loc["Steers 500 pounds and over", "Qty"]
    heifers = df.loc["Heifers 500 pounds and over", "Qty"]
    bulls = df.loc["Bulls 500 pounds and over", "Qty"]
    new_calves_per_year = df.loc["Calf crop", "Qty"]
    cattle_on_feed = df.loc["Cattle on feed", "Qty"]
    cow_slaughter_pm = df.loc["CowSlaughter", "Qty"]
    cowGestation = df.loc["cowGestation", "Qty"]
    calves_per_mother = 1

    #### Calcultaion for cows ratios
    # calaculate number of cows using ratios
    dairy_beef_mother_ratio = dairy_cows / beef_cows
    dairy_heifers = heifers * dairy_beef_mother_ratio
    beef_heifers = heifers - dairy_heifers

    dairy_calves = dairy_beef_mother_ratio * total_calves
    beef_calves = total_calves - dairy_calves
    dairy_calf_steers = dairy_calves / 2
    dairy_calf_girls = dairy_calves / 2

    calves_destined_for_beef_ratio = (beef_calves + dairy_calf_steers) / total_calves
    new_beef_calfs = calves_destined_for_beef_ratio * new_calves_per_year
    new_dairy_calfs = new_calves_per_year - new_beef_calfs
    new_beef_calfs_pm = new_beef_calfs / 12
    new_dairy_calfs_pm = new_dairy_calfs / 12

    cattle_in_beef_track = (
        dairy_calf_steers + beef_calves + beef_steers + beef_cows + beef_heifers
    )
    cattle_in_dairy_track = dairy_calf_girls + dairy_cows + dairy_heifers

    # other baseline variables
    dairy_life_expectancy = 5

    ## End cows, and basic animal variable defintiions ##

    # interventions, scale appropriately for maths (i.e convert sliders from % to decimal)
    reduction_in_beef_calves *= 0.01
    reduction_in_dairy_calves *= 0.01
    reduction_in_pig_breeding *= 0.01
    reduction_in_poultry_breeding *= 0.01
    increase_in_slaughter *= 0.01

    # per month values
    other_cow_death_rate = 0.005  # from USDA
    other_pig_death_rate = 0.005  # from USDA
    other_poultry_death_rate = 0.005
    new_beef_calfs_pm = new_beef_calfs / 12
    new_dairy_calfs_pm = new_dairy_calfs / 12
    new_pigs_pm = piglets_pm
    new_poultry_pm = chicks_pm

    # pregnant animals
    current_pregnant_sows = piglets_pm / piglets_per_litter
    current_pregnant_cows = new_beef_calfs_pm / calves_per_mother
    sow_slaughter_percent = mother_slaughter  # of total percent of pig slaughter
    mother_cow_slaughter_percent = mother_slaughter  # of total percent of cow slaughter

    #### Slaughtering ####
    ### Slaughtering variables (currently hardcoded !!)
    # total slaughter capacity
    cow_slaughter_hours = (
        4  # resources/hours of single person hours for slaughter of cow
    )
    pig_slaughter_hours = (
        4  # resources/hours of single person hours for slaughter of pig
    )
    poultry_slaughter_hours = (
        0.08  # resources/hours of single person hours for slaughter of poultry
    )
    total_slaughter_cap_hours = (
        cow_slaughter_pm * cow_slaughter_hours
        + pigs_slaughter_pm * pig_slaughter_hours
        + poultry_slaughter_pm * poultry_slaughter_hours
    )
    skill_transfer_discount_chickens_to_pigs = (100 - discount_rate) / 100  #
    skill_transfer_discount_pigs_to_cows = (100 - discount_rate) / 100  #

    ## Slaughtering Updates, increases from slider
    total_slaughter_cap_hours *= increase_in_slaughter  # measured in hours
    current_cow_slaughter = cow_slaughter_pm * increase_in_slaughter  # measured in head
    current_poultry_slaughter = (
        poultry_slaughter_pm * increase_in_slaughter
    )  # measured in head
    current_pig_slaughter = (
        pigs_slaughter_pm * increase_in_slaughter
    )  # measured in head
    spare_slaughter_hours = 0

    ## define current totals
    # current_beef_feed_cattle = cattle_on_feed
    current_beef_cattle = cattle_in_beef_track
    current_dairy_cattle = cattle_in_dairy_track
    current_total_pigs = total_pigs
    current_total_poultry = total_poultry

    ### FEED #commented out code is bottom up from roam page
    # beef_cow_feed_pm_per_cow = 880 # lbs
    # dairy_cow_feed_pm_per_cow = 1048
    # poultry_feed_pm_per_bird = 20
    # pig_feed_pm_per_pig = 139

    # these feed numbers are top down, calculations in google sheet, working backwards from total feed used and dividing it evenly amongst the animal populations
    beef_cow_feed_pm_per_cow = 137.3117552  # lbs
    dairy_cow_feed_pm_per_cow = 448.3820431
    poultry_feed_pm_per_bird = 4.763762808
    pig_feed_pm_per_pig = 141.8361586
    baseline_feed = (
        current_total_poultry * poultry_feed_pm_per_bird
        + current_total_pigs * pig_feed_pm_per_pig
        + current_beef_cattle * beef_cow_feed_pm_per_cow
        + dairy_cow_feed_pm_per_cow * current_dairy_cattle
    )

    d = []  # create empty list to place variables in to in loop

    # simulate x months
    for i in range(months):

        new_pigs_pm = current_pregnant_sows * piglets_per_litter
        new_beef_calfs_pm = current_pregnant_cows * calves_per_mother

        # determine birth rates
        if np.abs(i - cowGestation) <= 0.5:
            new_beef_calfs_pm *= 1 - reduction_in_beef_calves
            new_dairy_calfs_pm *= 1 - reduction_in_dairy_calves
            current_pregnant_cows *= 1 - reduction_in_beef_calves

        if np.abs(i - pigGestation) <= 0.5:
            new_pigs_pm *= 1 - reduction_in_pig_breeding
            current_pregnant_sows *= 1 - reduction_in_pig_breeding

        if np.abs(i - poultryGestation) <= 0.5:
            new_poultry_pm *= 1 - reduction_in_poultry_breeding

        if new_pigs_pm < 0:
            new_pigs_pm = 0

        if new_beef_calfs_pm < 0:
            new_beef_calfs_pm = 0

        # Transfer excess slaughter capacity to next animal, current coding method only allows poultry -> pig -> cow, there are some small erros here due to rounding, and the method is not 100% water tight but errors are within the noise
        if current_total_poultry < current_poultry_slaughter:
            spare_slaughter_hours = (
                current_poultry_slaughter - current_total_poultry
            ) * poultry_slaughter_hours
            current_poultry_slaughter = current_total_poultry
            current_pig_slaughter += (
                spare_slaughter_hours
                * skill_transfer_discount_chickens_to_pigs
                / pig_slaughter_hours
            )
        if current_total_pigs < current_pig_slaughter:
            spare_slaughter_hours = (
                current_pig_slaughter - current_total_pigs
            ) * pig_slaughter_hours
            current_pig_slaughter = current_total_pigs
            current_cow_slaughter += (
                spare_slaughter_hours
                * skill_transfer_discount_pigs_to_cows
                / cow_slaughter_hours
            )

        # this set up only kills dairy cows when they are getting to the end of their life.
        current_dairy_slaughter = current_dairy_cattle / (dairy_life_expectancy * 12)
        current_beef_slaughter = current_cow_slaughter - current_dairy_slaughter
        if current_beef_cattle < current_beef_slaughter:
            actual_beef_slaughter = current_beef_cattle  # required due to the difference between actual slaughter and 'slaughter capacity' consider a rewrite of the whole method to distinuguish between these two. For now, this is thr workaround.
        else:
            actual_beef_slaughter = current_beef_slaughter

        other_beef_death = other_cow_death_rate * current_beef_cattle
        other_dairy_death = other_cow_death_rate * current_dairy_cattle
        other_pig_death = current_total_pigs * other_pig_death_rate
        other_poultry_death = current_total_poultry * other_poultry_death_rate

        ## Feed
        current_beef_feed = current_beef_cattle * beef_cow_feed_pm_per_cow
        current_dairy_feed = current_dairy_cattle * dairy_cow_feed_pm_per_cow
        current_pig_feed = current_total_pigs * pig_feed_pm_per_pig
        current_poultry_feed = current_total_poultry * poultry_feed_pm_per_bird
        current_feed_combined = (
            current_beef_feed
            + current_dairy_feed
            + current_pig_feed
            + current_poultry_feed
        )
        current_feed_saved = baseline_feed - current_feed_combined


        ### Generate list (before new totals have been calculated)
        # magnitude adjust moves the numbers from per thousnad head to per head (or other)
        # feed adjust turns lbs in to tons
        d.append(
            {
                "Beef Pop": current_beef_cattle * magnitude_adjust,
                "Beef Born": new_beef_calfs_pm * magnitude_adjust,
                "Beef Slaughtered": actual_beef_slaughter * magnitude_adjust,
                "Beef Slaughtered Hours": actual_beef_slaughter
                * cow_slaughter_hours
                * magnitude_adjust,
                "Beef Slaughtered Hours %": actual_beef_slaughter
                * cow_slaughter_hours
                / total_slaughter_cap_hours,
                "Beef Other Death": other_beef_death * magnitude_adjust,
                "Beef Feed": current_beef_cattle
                * beef_cow_feed_pm_per_cow
                * magnitude_adjust
                * feed_unit_adjust,
                "Dairy Pop": current_dairy_cattle * magnitude_adjust,
                "Dairy Born": new_dairy_calfs_pm * magnitude_adjust,
                "Dairy Slaughtered": current_dairy_slaughter * magnitude_adjust,
                "Dairy Slaughtered Hours": current_dairy_slaughter
                * cow_slaughter_hours
                * magnitude_adjust,
                "Dairy Slaughtered Hours %": current_dairy_slaughter
                * cow_slaughter_hours
                / total_slaughter_cap_hours,
                "Dairy Other Death": other_dairy_death * magnitude_adjust,
                "Dairy Feed": current_dairy_cattle
                * dairy_cow_feed_pm_per_cow
                * magnitude_adjust
                * feed_unit_adjust,
                "Pigs Pop": current_total_pigs * magnitude_adjust,
                "Pig Born": new_pigs_pm * magnitude_adjust,
                "Pig Slaughtered": current_pig_slaughter * magnitude_adjust,
                "Pig Slaughtered Hours": current_pig_slaughter
                * pig_slaughter_hours
                * magnitude_adjust,
                "Pig Slaughtered Hours %": current_pig_slaughter
                * pig_slaughter_hours
                / total_slaughter_cap_hours,
                "Pigs Feed": current_total_pigs
                * pig_feed_pm_per_pig
                * magnitude_adjust
                * feed_unit_adjust,
                "Poultry Pop": current_total_poultry
                / poultry_visual_optimiser
                * magnitude_adjust,
                "Poultry Born": new_poultry_pm
                / poultry_visual_optimiser
                * magnitude_adjust,
                "Poultry Slaughtered": current_poultry_slaughter
                / poultry_visual_optimiser
                * magnitude_adjust,
                "Poultry Slaughtered Hours": current_poultry_slaughter
                * poultry_slaughter_hours
                * magnitude_adjust,
                "Poultry Slaughtered Hours %": current_poultry_slaughter
                * poultry_slaughter_hours
                / total_slaughter_cap_hours,
                "Poultry Feed": current_total_poultry
                * poultry_feed_pm_per_bird
                * magnitude_adjust
                * feed_unit_adjust,
                "Combined Feed": current_feed_combined
                * magnitude_adjust
                * feed_unit_adjust,
                "Combined Saved Feed": (baseline_feed - current_feed_combined)
                * magnitude_adjust
                * feed_unit_adjust,
                "Month": i,
            }
        )

        # some up new totals
        current_beef_cattle += (
            new_beef_calfs_pm - current_beef_slaughter - other_beef_death
        )
        current_dairy_cattle += (
            new_dairy_calfs_pm - current_dairy_slaughter - other_dairy_death
        )
        current_total_poultry += (
            new_poultry_pm - current_poultry_slaughter - other_poultry_death
        )
        current_total_pigs += new_pigs_pm - current_pig_slaughter - other_pig_death

        current_pregnant_sows -= sow_slaughter_percent * (
            current_pig_slaughter + other_pig_death
        )
        current_pregnant_cows -= mother_cow_slaughter_percent * (
            current_beef_slaughter + other_beef_death
        )

        if current_beef_cattle < 0:
            current_beef_cattle = 0
        if current_dairy_cattle < 0:
            current_dairy_cattle = 0

    ### End of loop, start summary

    df_final = pd.DataFrame(d)

    # final feed calculations
    total_feed_saved = (df_final["Combined Saved Feed"]).sum()  # million tons
    baseline_total_feed = baseline_feed * magnitude_adjust * feed_unit_adjust * months

    # create figures
    fig1 = px.line(
        df_final, x="Month", y=["Beef Born", "Dairy Born", "Pig Born", "Poultry Born"]
    )  # range_y=[0000,100000]
    fig2 = px.bar(
        df_final,
        x="Month",
        y=["Beef Pop", "Dairy Pop", "Pigs Pop", "Poultry Pop"],
        title="Population Make-up",
    )
    fig3 = px.bar(
        df_final,
        x="Month",
        y=["Beef Feed", "Dairy Feed", "Pigs Feed", "Poultry Feed"],
        title="Feed Requirements (Dry Matter Equivalent)",
    )
    fig4 = px.bar(
        df_final,
        x="Month",
        y=[
            "Beef Slaughtered Hours %",
            "Dairy Slaughtered Hours %",
            "Pig Slaughtered Hours %",
            "Poultry Slaughtered Hours %",
        ],
        title="Slaughter Worker Hours Distribution Percentage",
    )
    fig5 = px.bar(
        df_final,
        x="Month",
        y=[
            "Beef Slaughtered",
            "Dairy Slaughtered",
            "Pig Slaughtered",
            "Poultry Slaughtered",
        ],
        title="Slaughter Counts Distribution",
    )
    fig6 = px.line(df_final, x="Month", y=["Combined Feed"])

    # return figures and outputs
    return (
        fig1,
        fig2,
        fig3,
        fig4,
        fig5,
        fig6,
        f"# Total Feed Use Reduction over {months} months is {(total_feed_saved/1000000).round() } Mtons from a baseline of {(baseline_total_feed/1000000).round()} Mtons"
        # "Modelled beef and dairy industry",
    )  # returned objects are assigned to the component property of the Output


# Run app
if __name__ == "__main__":
    app.run_server(debug=False, port=8055)
