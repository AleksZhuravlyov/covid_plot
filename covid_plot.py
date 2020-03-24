import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import sqlite3


parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
parser.add_argument('--log', default=True, action='store_true', help='set logarithmic scale for Y axis')
parser.add_argument('--list', action='store_true', help='get list of available countries')
parser.add_argument('--countries', type=str, nargs='+', default=['Russia'],
                    help='set list of countries to be plotted')

args = parser.parse_args()

cwd = os. getcwd()
base_path = "COVID-19/data"
cases_file_name = "cases_time.csv"

if os.path.isdir(base_path):
    os.chdir(base_path)
    os.system("git pull")
    os.chdir(cwd)
else:
    os.system("git clone https://github.com/CSSEGISandData/COVID-19")
    os.chdir('COVID-19')
    os.system("git checkout web-data")
    os.chdir("..")

try:
    conn = sqlite3.connect(':memory:')
except sqlite3.Error as e:
    print(e)
    sys.exit(-2)

cases = pd.read_csv(os.path.join(base_path, cases_file_name))
all_countries = sorted(set(cases['Country_Region'].values.tolist()))

countries = sorted(list(set(all_countries) & set(args.countries)))

if len(countries) == 0 :
    print("No known countries were specified. Should be in ", file=sys.stderr)
    print(all_countries, file=sys.stderr)
    sys.exit(-1)

if args.list:
    print(all_countries)
    sys.exit(0)

cases['Last_Update'] = pd.to_datetime(cases['Last_Update'])
cases.to_sql("pandas_cases", conn)


fig, ax = plt.subplots()
for country in countries:
    # plot country
    ddd = pd.read_sql_query(f"SELECT * from pandas_cases where Country_Region in ({','.join(['?']*len([country]))}) order by Country_Region ASC, Last_Update ASC", conn, params=[country])
    color = next(ax._get_lines.prop_cycler)['color']
    ddd['Last_Update'] = pd.to_datetime(ddd['Last_Update'])
    ddd.plot(x='Last_Update', y='Confirmed', linestyle='-', color=color,ax=ax, label=country)
    ddd.plot(x='Last_Update', y='Deaths', linestyle='--', label='_nolegend_', color=color,ax=ax)


handles, labels = ax.get_legend_handles_labels()
legend = ax.legend()
for handle in legend.legendHandles:
    handle.set_linewidth(5.0)

plt.ylabel('people')

if args.log:
    plt.yscale("log")

plt.title('Confirmed Cases (—) and Deaths (---)')

plt.grid(True)


plt.show()
