from __future__ import print_function
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import itertools


parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
parser.add_argument('--log', action='store_true', help='set logarithmic scale for Y axis')
parser.add_argument('--list', action='store_true', help='get list iof available countries')
parser.add_argument('--countries', type=str, nargs='+', default=['Russia'], help='set list of countries to be plotted')

args = parser.parse_args()

base_path = "COVID-19/csse_covid_19_data/csse_covid_19_time_series"
confirmed_file_name = "time_series_19-covid-Confirmed.csv"
deaths_file_name = "time_series_19-covid-Deaths.csv"

if os.path.isdir(base_path):
    os.chdir(base_path)
    os.system("git pull")
else:
    os.system("git clone https://github.com/CSSEGISandData/COVID-19")
    os.chdir
    
confirmed = pd.read_csv(confirmed_file_name)
deaths = pd.read_csv(deaths_file_name)

os.chdir("../../..")

confirmed.index = confirmed['Country/Region']
deaths.index = deaths['Country/Region']

drop_columns = ['Lat', 'Long', 'Province/State', 'Country/Region']
confirmed = confirmed.drop(columns=drop_columns)
deaths = deaths.drop(columns=drop_columns)

confirmed.columns = pd.to_datetime(confirmed.columns)
deaths.columns = pd.to_datetime(deaths.columns)

if args.list:
    
    print(sorted(set(confirmed.index.tolist())))
    
else:
    
    countries = list()
    for country in args.countries:
        
        if country not in confirmed.index:
           print(country + ' is not in the set of countries', file=sys.stderr)
           continue
        countries.append({'confirmed': confirmed.loc[country], 'deaths': deaths.loc[country]})
        
        if isinstance(countries[-1]['confirmed'], pd.DataFrame):
            countries[-1]['confirmed'] = countries[-1]['confirmed'].sum(axis = 0, skipna = True)
            countries[-1]['confirmed'].name = country
        countries[-1]['confirmed'] = countries[-1]['confirmed'][countries[-1]['confirmed']!=0]
        
        if isinstance(countries[-1]['deaths'], pd.DataFrame):
            countries[-1]['deaths'] = countries[-1]['deaths'].sum(axis = 0, skipna = True)
            countries[-1]['deaths'].name = country
        countries[-1]['deaths'] = countries[-1]['deaths'][countries[-1]['deaths']!=0]
    
    if len(countries) == 0:
        sys.exit(0)
    
    fig, ax = plt.subplots()
    for country in countries:
        # plot country
        color = next(ax._get_lines.prop_cycler)['color']
        country['confirmed'].plot(linestyle='-', color = color)
        country['deaths'].plot(linestyle='--', label='_nolegend_', color = color)
    
    
    handles, labels = ax.get_legend_handles_labels()
    
    handles[-1].color='b'
    
    print(labels)
    
    legend = ax.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)    
    
    plt.ylabel('people')
    
    if args.log:
        plt.yscale("log")
    
    plt.title('Confirmed Cases and Deaths')
    
    plt.grid(True)    
    
    plt.show()
    