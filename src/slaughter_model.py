import pandas as pd


path    = "../data/NassCattle2022.csv"
df      = pd.read_csv(path)


df.set_index("Variable",
            inplace = True)

print(df.loc["Beef cows"])




df.loc["Beef cows","Qty"]
df.loc['Cattle and calves',"Qty"]

df["Qty"] = df["Qty"].astype("float") 

starting_herd_size  = df.loc['Cattle and calves',"Qty"]
total_calves        = df.loc["Calves under 500 pounds","Qty"]
dairy_cows          = df.loc["Milk cows","Qty"]
beef_cows           = df.loc["Beef cows","Qty"]
beef_steers         = df.loc["Steers 500 pounds and over","Qty"]
heifers             = df.loc["Heifers 500 pounds and over","Qty"]
bulls               = df.loc["Bulls 500 pounds and over","Qty"]
new_calves_per_year = df.loc["Calf crop","Qty"]


dairy_beef__mother_ratio    = dairy_cows/beef_cows
dairy_heifers       = heifers*dairy_beef_ratio
beef_heifers        = heifers-dairy_heifers

dairy_calves        = dairy_beef_ratio*total_calves
beef_calves         = total_calves-dairy_calves
dairy_calf_steers   = dairy_calves/2
dairy_calf_girls    = dairy_calves/2

calves_destined_for_beef_ratio = (beef_calves+dairy_calf_steers)/total_calves
new_beef_calfs       = calves_destined_for_beef_ratio*new_calves_per_year

cattle_in_beef_track = dairy_calf_steers+beef_calves+beef_steers+beef_cows + beef_heifers
cattle_in_dairy_rack = dairy_calf_girls+dairy_cows+dairy_heifers


# other baseline variables
slaughtering_pm = 2900



# interventions
reduction_in_beef_calves = 0.8
reduction_in_dairy_calves = 0.2

#per month
new_beef_calfs_pm = new_beef_calfs/12


cows_slaughtered_max_month = 2900 # from historical surge data


# pm = per month
true_beef_pm = true_beef_calves/12

dairy_life_exp = 7
dairy_cull_slaughter_pm = dairy_mothers/(7*12)








life_exp_dairy = 7
life_exp_beef = 2

current_herd = starting_herd_size




# months = 6
# for i in range(months):

#     current_herd - net_change
#     print(i)






