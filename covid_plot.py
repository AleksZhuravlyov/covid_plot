from __future__ import print_function
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse


parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
parser.add_argument('--log', default=False, action='store_true', help='set logarithmic scale for Y axis')
parser.add_argument('--list', default=False, action='store_true', help='get list iof available countries')
parser.add_argument('--countries', type=str, nargs='+', default=['Russia'], help='set list of countries to be plotted')

args = parser.parse_args()

base_path = "COVID-19/csse_covid_19_data/csse_covid_19_time_series"
confirmed_file_name = "time_series_19-covid-Confirmed.csv"

if os.path.isdir(base_path):
    os.chdir(base_path)
    os.system("git pull")
else:
    os.system("git clone https://github.com/CSSEGISandData/COVID-19")
    os.chdir
    
confirmed = pd.read_csv(confirmed_file_name)
os.chdir("../../..")
confirmed.index = confirmed['Country/Region']
confirmed = confirmed.drop(columns=['Lat', 'Long', 'Province/State', 'Country/Region'])

confirmed.columns = pd.to_datetime(confirmed.columns)

if args.country_list:
    
    print(sorted(set(confirmed.index.tolist())))
    
else:
    
    countries = list()
    for country in args.countries:
        if country not in confirmed.index:
           print(country + ' is not in the set of countries', file=sys.stderr)
           continue
        countries.append(confirmed.loc[country])
        if isinstance(countries[-1], pd.DataFrame):
            countries[-1] = countries[-1].sum(axis = 0, skipna = True)
            countries[-1].name = country
        countries[-1] = countries[-1][countries[-1]!=0]
    
    if len(countries) == 0:
        sys.exit(0)
    
    for country in countries:
        # plot country
        ax = country.plot(marker='o', markersize=2, legend=True)
        ax.legend()    
    
    plt.ylabel('people')
    
    if args.log:
        plt.yscale("log")
    
    plt.title('Confirmed Cases')
    
    plt.grid(True)
    
    plt.show()
    