import os
import sys
from io import StringIO
import matplotlib.pyplot as plt
import pandas as pd
import argparse


parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
parser.add_argument("--log", type=bool, default=True, help="Logarithmic scale for Y axis")
parser.add_argument("--countries", type=str, nargs="+", default=["Russia"], help="List of countries to be plotted.")

args = parser.parse_args()

base_path = "COVID-19/csse_covid_19_data/csse_covid_19_time_series"
confirmed_file_name = "time_series_19-covid-Confirmed.csv"

if os.path.isdir(base_path):
    os.chdir(base_path)
    os.system("git pull")
else:
    os.system("git clone https://github.com/CSSEGISandData/COVID-19")
    os.chdir(base_path)

confirmed = pd.read_csv(confirmed_file_name)
os.chdir("../../..")
confirmed.index = confirmed['Country/Region']
confirmed = confirmed.drop(columns=['Lat', 'Long', 'Province/State', 'Country/Region'])

confirmed.columns = pd.to_datetime(confirmed.columns)

countries_set = set(confirmed.index.tolist())

for country in args.countries:
    if country not in countries_set:
        sys.exit(country + ' is not in the set of countries')

countries = list()        
for country in args.countries:
    countries.append(confirmed.loc[country])
    if isinstance(countries[-1], pd.DataFrame):
        countries[-1] = countries[-1].sum(axis = 0, skipna = True)
        countries[-1].name = country
    countries[-1] = countries[-1][countries[-1]!=0]

for country in countries:
    ax = country.plot(marker='o', markersize=2, legend=True)
ax.set_ylabel('people')       

if args.log == True:
    plt.yscale("log")

plt.title('Confirmed Cases')

plt.grid(True)
    
plt.show()
