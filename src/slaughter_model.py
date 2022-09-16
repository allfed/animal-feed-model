import pandas as pd


path    = "../data/NassCattle2022.csv"
df      = pd.read_csv(path)

df.set_index("Variable",
            inplace = True)

print("hello world")



months = 6
for i in range(months):
    print(i)






