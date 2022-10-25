import pathlib
import plotly.express as px
import pandas as pd
from difflib import diff_bytes
import numpy as np
from dash import Dash, dcc, html, Output, Input, dash_table  # pip install dash
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components
import matplotlib.pyplot as plt

plt.style.use(
    "https://raw.githubusercontent.com/allfed/ALLFED-matplotlib-style-sheet/main/ALLFED.mplstyle"
)


# CSV changes
# changes to head/1000 head
# dash vs matplotlib


"""
Define functions
"""


def create_plotly_figs(df_final):

    graph_colours = ["#3D87CB", "#F0B323", "#DC582A", "#674230", "#3A913F", "#75787B"]
    # create figures
    fig1 = px.line(
        df_final,
        x="Month",
        y=["Beef Born", "Dairy Born", "Pig Born", "Poultry Born"],
        color_discrete_sequence=graph_colours,
    ).update_layout(yaxis_title="Head")
    fig2 = px.bar(
        df_final,
        x="Month",
        y=["Beef Pop", "Dairy Pop", "Pigs Pop", "Poultry Pop"],
        title="Population Make-up",
        color_discrete_sequence=graph_colours,
    ).update_layout(yaxis_title="Head")
    fig3 = px.bar(
        df_final,
        x="Month",
        y=["Beef Feed", "Dairy Feed", "Pigs Feed", "Poultry Feed"],
        title="Feed Requirements",
        color_discrete_sequence=graph_colours,
    ).update_layout(yaxis_title="Metric Tonnes")
    fig4 = px.bar(
        df_final,
        x="Month",
        y=[
            "Beef Slaughtered Hours %",
            "Dairy Slaughtered Hours %",
            "Pig Slaughtered Hours %",
            "Poultry Slaughtered Hours %",
        ],
        title="Slaughter Worker Hours Fractional Distribution",
        color_discrete_sequence=graph_colours,
    ).update_layout(yaxis_title="Fraction Hours")
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
        color_discrete_sequence=graph_colours,
    ).update_layout(yaxis_title="Head")
    fig6 = px.line(df_final, x="Month", y=["Combined Feed"])

    return (fig1, fig2, fig3, fig4, fig5, fig6)


def calculate_feed_and_animals(
    reduction_in_beef_calves,
    reduction_in_dairy_calves,
    increase_in_slaughter,
    reduction_in_pig_breeding,
    reduction_in_poultry_breeding,
    months,
    discount_rate,
    mother_slaughter,
    use_grass_and_residues_for_dairy,
    animal_inputs,
):  # function arguments come from the component property of the Input (in this case, the sliders)

    tons_to_kcals = (
        (3560 + 3350) / 2 * 1000
    )  # convert tons to kcals (ASSUME CALORIC DENSITY IS HALF MAIZE, HALF SOYBEAN)
    kcals_to_billion_kcals = 1e-9
    feed_unit_adjust = (
        0.000453592 * tons_to_kcals * kcals_to_billion_kcals
    )  # convert pounds to tonnes to billions of kcals
    ## unpack all the dataframe information for ease of use ##
    # pigs
    total_pigs = animal_inputs.dataframe.loc["TotalPigs", "Qty"]
    piglets_pm = animal_inputs.dataframe.loc["PigletsPerMonth", "Qty"]
    pigs_slaughter_pm = animal_inputs.dataframe.loc["SlaughterPerMonth", "Qty"]
    pigGestation = animal_inputs.dataframe.loc["pigGestation", "Qty"]
    piglets_per_litter = animal_inputs.dataframe.loc["PigsPerLitter", "Qty"]

    # poultry
    total_poultry = animal_inputs.dataframe.loc["Broiler Population", "Qty"]
    poultry_slaughter_pm = animal_inputs.dataframe.loc[
        "poultry_slaughter_pm", "Qty"
    ]  # USDA
    chicks_pm = poultry_slaughter_pm  # assume the same, no data
    poultryGestation = animal_inputs.dataframe.loc[
        "Chicken Gestation", "Qty"
    ]  # USDA  # actaully 21 days, let's round to 1 month

    # cows (more complex, as need to split dairy and beef)
    total_calves = animal_inputs.dataframe.loc["Calves under 500 pounds", "Qty"]
    dairy_cows = animal_inputs.dataframe.loc["Milk cows", "Qty"]
    beef_cows = animal_inputs.dataframe.loc["Beef cows", "Qty"]
    beef_steers = animal_inputs.dataframe.loc["Steers 500 pounds and over", "Qty"]
    heifers = animal_inputs.dataframe.loc["Heifers 500 pounds and over", "Qty"]
    bulls = animal_inputs.dataframe.loc["Bulls 500 pounds and over", "Qty"]
    new_calves_per_year = animal_inputs.dataframe.loc["Calf crop", "Qty"]
    cattle_on_feed = animal_inputs.dataframe.loc["Cattle on feed", "Qty"]
    cow_slaughter_pm = animal_inputs.dataframe.loc["CowSlaughter", "Qty"]
    cowGestation = animal_inputs.dataframe.loc["cowGestation", "Qty"]
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
    if use_grass_and_residues_for_dairy:
        dairy_cow_feed_pm_per_cow = 0
    else:
        dairy_cow_feed_pm_per_cow = 448.3820431
    poultry_feed_pm_per_bird = 4.763762808
    pig_feed_pm_per_pig = 141.8361586
    baseline_feed = (
        current_total_poultry * poultry_feed_pm_per_bird
        + current_total_pigs * pig_feed_pm_per_pig
        + current_beef_cattle * beef_cow_feed_pm_per_cow
        + current_dairy_cattle * dairy_cow_feed_pm_per_cow
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

        print(current_poultry_feed * feed_unit_adjust)
        print(current_feed_combined * feed_unit_adjust)

        ### Generate list (before new totals have been calculated)
        # magnitude adjust moves the numbers from per thousnad head to per head (or other)
        # feed adjust turns lbs in to tons
        d.append(
            {
                "Beef Pop": current_beef_cattle,
                "Beef Born": new_beef_calfs_pm,
                "Beef Slaughtered": actual_beef_slaughter,
                "Beef Slaughtered Hours": actual_beef_slaughter * cow_slaughter_hours,
                "Beef Slaughtered Hours %": actual_beef_slaughter
                * cow_slaughter_hours
                / total_slaughter_cap_hours,
                "Beef Other Death": other_beef_death,
                "Beef Feed": current_beef_cattle
                * beef_cow_feed_pm_per_cow
                * feed_unit_adjust,
                "Dairy Pop": current_dairy_cattle,
                "Dairy Born": new_dairy_calfs_pm,
                "Dairy Slaughtered": current_dairy_slaughter,
                "Dairy Slaughtered Hours": current_dairy_slaughter
                * cow_slaughter_hours,
                "Dairy Slaughtered Hours %": current_dairy_slaughter
                * cow_slaughter_hours
                / total_slaughter_cap_hours,
                "Dairy Other Death": other_dairy_death,
                "Dairy Feed": current_dairy_cattle
                * dairy_cow_feed_pm_per_cow
                * feed_unit_adjust,
                "Pigs Pop": current_total_pigs,
                "Pig Born": new_pigs_pm,
                "Pig Slaughtered": current_pig_slaughter,
                "Pig Slaughtered Hours": current_pig_slaughter * pig_slaughter_hours,
                "Pig Slaughtered Hours %": current_pig_slaughter
                * pig_slaughter_hours
                / total_slaughter_cap_hours,
                "Pigs Feed": current_total_pigs
                * pig_feed_pm_per_pig
                * feed_unit_adjust,
                "Poultry Pop": current_total_poultry,
                "Poultry Born": new_poultry_pm,
                "Poultry Slaughtered": current_poultry_slaughter,
                "Poultry Slaughtered Hours": current_poultry_slaughter
                * poultry_slaughter_hours,
                "Poultry Slaughtered Hours %": current_poultry_slaughter
                * poultry_slaughter_hours
                / total_slaughter_cap_hours,
                "Poultry Feed": current_total_poultry
                * poultry_feed_pm_per_bird
                * feed_unit_adjust,
                "Combined Feed": current_feed_combined * feed_unit_adjust,
                "Combined Saved Feed": (baseline_feed - current_feed_combined)
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

    return df_final


"""
Defne Classes
"""


class ModelAnimalInputs:
    def __init__(self, dataframe):
        self.dataframe = dataframe


class ModelSlidersDefaults:
    def __init__(self, dataframe):
        self.reduction_in_beef_calves = dataframe.loc["reduction_in_beef_calves", "Qty"]
        self.reduction_in_dairy_calves = dataframe.loc[
            "reduction_in_dairy_calves", "Qty"
        ]
        self.change_to_baseline_slaughter = dataframe.loc[
            "change_to_baseline_slaughter", "Qty"
        ]
        self.reduction_in_pig_breeding = dataframe.loc[
            "reduction_in_pig_breeding", "Qty"
        ]
        self.reduction_in_poultry_breeding = dataframe.loc[
            "reduction_in_poultry_breeding", "Qty"
        ]
        self.months = dataframe.loc["months", "Qty"]
        self.discount_rate = dataframe.loc["discount_rate", "Qty"]
        self.mother_slaughter = dataframe.loc["mother_slaughter", "Qty"]
        self.use_grass_and_residues_for_dairy = dataframe.loc[
            "use_grass_and_residues_for_dairy", "Qty"
        ]


class ModelSliderInputs:
    def __init__(self, dataframe):
        self.reduction_in_beef_calves = dataframe.loc["reduction_in_beef_calves", "Qty"]
        self.reduction_in_dairy_calves = dataframe.loc[
            "reduction_in_dairy_calves", "Qty"
        ]
        self.change_to_baseline_slaughter = dataframe.loc[
            "change_to_baseline_slaughter", "Qty"
        ]
        self.reduction_in_pig_breeding = dataframe.loc[
            "reduction_in_pig_breeding", "Qty"
        ]
        self.reduction_in_poultry_breeding = dataframe.loc[
            "reduction_in_poultry_breeding", "Qty"
        ]
        self.months = dataframe.loc["months", "Qty"]
        self.discount_rate = dataframe.loc["discount_rate", "Qty"]
        self.mother_slaughter = dataframe.loc["mother_slaughter", "Qty"]
        self.use_grass_and_residues_for_dairy = dataframe.loc[
            "use_grass_and_residues_for_dairy", "Qty"
        ]


"""
Start main function
"""
# Import CSV to dataframes
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()
df_animals = pd.read_csv(
    DATA_PATH.joinpath("InputDataAndSources.csv"), index_col="Variable"
)

## various scenarios can be used here
df_baseline_vars = pd.read_csv(
    DATA_PATH.joinpath("default_slider_values.csv"), index_col="Variable"
)  # change this to saved model values (optimistic/pessimistic etc.)
df_optimistic_vars = pd.read_csv(
    DATA_PATH.joinpath("optimistic_slider_values.csv"), index_col="Variable"
)  # change this to saved model values (optimistic/pessimistic etc.)
df_pessimistic_vars = pd.read_csv(
    DATA_PATH.joinpath("default_slider_values.csv"), index_col="Variable"
)  # change this to saved model values (optimistic/pessimistic etc.)

## poplulate the data in to classes
animal_inputs = ModelAnimalInputs(df_animals)
slider_inputs = ModelSlidersDefaults(
    df_baseline_vars
)  #### THIS IS THE SCENARIO CHOOSER


df_final = calculate_feed_and_animals(
    slider_inputs.reduction_in_beef_calves,
    slider_inputs.reduction_in_dairy_calves,
    slider_inputs.change_to_baseline_slaughter,
    slider_inputs.reduction_in_pig_breeding,
    slider_inputs.reduction_in_poultry_breeding,
    slider_inputs.months,
    slider_inputs.discount_rate,
    slider_inputs.mother_slaughter,
    slider_inputs.use_grass_and_residues_for_dairy,
    animal_inputs,
)

## Example of matplotlib plotting ##

plt.figure()
plt.plot(df_final["Combined Feed"])
plt.title("Combined Feed")
plt.show()

### End Model Section ###

# ### Start DASH section ###
## Currently commented out, need to seperate in to packages to avoid this I believe


# #### Do Dash things below, skip ahead to callback function for the main event
# # Build your components
# app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# # Declare server for Heroku deployment. Needed for Procfile.
# server = app.server  # for heroku deployment

# mytitle = dcc.Markdown(children="")
# # table_out = dcc.Markdown(children="")
# # mysubtitle = dcc.Markdown(children="")
# scatter = dcc.Graph(figure={})
# scatter2 = dcc.Graph(figure={})
# bar = dcc.Graph(figure={})
# bar2 = dcc.Graph(figure={})
# bar3 = dcc.Graph(figure={})
# bar4 = dcc.Graph(figure={})

# ### Create slider components on a card
# controls = dbc.Card(
#     [
#         html.Div(
#             [
#                 dbc.Label("Baseline Slaughter Rate"),
#                 dcc.Slider(
#                     0,
#                     600,
#                     value=slider_inputs.change_to_baseline_slaughter,
#                     id="myslider3",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label(
#                     "Proportion of Slaughter which is mothers"
#                 ),  # (proxy for termination of pregnancies too, but not the same as a percentage)
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.mother_slaughter,
#                     id="myslider8",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label(
#                     "Discount Rate for Labour/Technology Transfer between species"
#                 ),
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.discount_rate,
#                     id="myslider7",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Decrease Beef Birth Rate"),
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.reduction_in_beef_calves,
#                     id="myslider1",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Decrease Dairy Birth Rate"),
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.reduction_in_dairy_calves,
#                     id="myslider2",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Reduction Pig Breeding"),
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.reduction_in_pig_breeding,
#                     id="myslider4",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Reduction Poultry Breeding"),
#                 dcc.Slider(
#                     0,
#                     100,
#                     value=slider_inputs.reduction_in_poultry_breeding,
#                     id="myslider5",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Use Residues for Dairy"),
#                 dcc.Slider(
#                     0,
#                     1,
#                     value=slider_inputs.use_grass_and_residues_for_dairy,
#                     step=1,
#                     id="myslider9",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#         html.Div(
#             [
#                 dbc.Label("Months"),
#                 dcc.Slider(
#                     0,
#                     24,
#                     value=slider_inputs.months,
#                     step=1,
#                     id="myslider6",
#                     updatemode="drag",
#                     tooltip={"placement": "bottom", "always_visible": True},
#                 ),
#             ]
#         ),
#     ],
#     body=True,
# )


# # Customize your own Layout
# app.layout = dbc.Container(
#     [
#         dbc.Row([dbc.Col([mytitle], width=6)], justify="center"),
#         # dbc.Row([dbc.Col([mysubtitle], width=6)], justify="center"),
#         dbc.Row(
#             [
#                 dbc.Col(controls, md=3),
#                 dbc.Col([bar], width=9),
#             ],
#             align="center",
#         ),
#         html.Hr(),
#         dbc.Row([dbc.Col([bar2], width=12)], justify="center"),
#         dbc.Row([dbc.Col([bar3], width=12)], justify="center"),
#         dbc.Row([dbc.Col([bar4], width=12)], justify="center"),
#         dbc.Row([dbc.Col([scatter], width=12)], justify="center"),
#         dbc.Row([dbc.Col([scatter2], width=12)], justify="center"),

#     ],
#     fluid=True,
# )


# #### Callback function here, this is where it all happens
# # Callback allows components to interact plotly
# @app.callback(
#     Output(scatter, "figure"),
#     Output(bar, "figure"),
#     Output(bar2, "figure"),
#     Output(bar3, "figure"),
#     Output(bar4, "figure"),
#     Output(scatter2, "figure"),
#     Output(mytitle, "children"),
#     # Output(table_out, "children"),
#     # Output(mysubtitle, "children"),
#     Input("myslider1", "value"),
#     Input("myslider2", "value"),
#     Input("myslider3", "value"),
#     Input("myslider4", "value"),
#     Input("myslider5", "value"),
#     Input("myslider6", "value"),
#     Input("myslider7", "value"),
#     Input("myslider8", "value"),
#     Input("myslider9", "value"),
# )
# #### Update graphs functions plotly ####
# def update_graph(
#     reduction_in_beef_calves,
#     reduction_in_dairy_calves,
#     change_to_baseline_slaughter,
#     reduction_in_pig_breeding,
#     reduction_in_poultry_breeding,
#     months,
#     discount_rate,
#     mother_slaughter,
#     use_grass_and_residues_for_dairy
# ):  # function arguments come from the component property of the Input (in this case, the sliders)

#     ## Run Model ##
#     df_final = calculate_feed_and_animals(
#         reduction_in_beef_calves,
#         reduction_in_dairy_calves,
#         change_to_baseline_slaughter,
#         reduction_in_pig_breeding,
#         reduction_in_poultry_breeding,
#         months,
#         discount_rate,
#         mother_slaughter,
#         use_grass_and_residues_for_dairy,
#         animal_inputs
#     )

#     ## Create figures ##
#     [fig1,fig2,fig3,fig4,fig5,fig6] = create_plotly_figs(df_final)
#     # return figures and outputs
#     return (
#         fig1,
#         fig2,
#         fig3,
#         fig4,
#         fig5,
#         fig6,
#         "Animal Feed Model"
#         # f"# Total Feed Use Reduction over {months} months is {months} million tonnes from a baseline of {months} million tonnes",
#     )  # returned objects are assigned to the component property of the Output

# # Run app
# if __name__ == "__main__":
#     app.run_server(debug=False, port=8055)
