import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import sqlite3


def process(args, connection):
    cases = pd.read_csv(os.path.join(base_path, cases_file_name))
    all_countries = sorted(set(cases['Country_Region'].values.tolist()))
    # filter out unknown countries
    countries = sorted(list(set(all_countries) & set(args.countries)))

    if len(countries) == 0:
        print("No known countries were specified. Should be in ", file=sys.stderr)
        print(all_countries, file=sys.stderr)
        sys.exit(-1)

    if args.list:
        print(all_countries)
        sys.exit(0)

    cases['Last_Update'] = pd.to_datetime(cases['Last_Update'])
    cases.to_sql("pandas_cases", connection)

    fig, ax = plt.subplots()
    for country in countries:
        # plot country
        cases_time = pd.read_sql_query(
            f'SELECT * from pandas_cases where Country_Region in (?) order by Last_Update ASC',
            connection, params=[country])
        color = next(ax._get_lines.prop_cycler)['color']
        cases_time['Last_Update'] = pd.to_datetime(cases_time['Last_Update'])
        cases_time.plot(x='Last_Update', y='Confirmed', linestyle='-', color=color, ax=ax, label=country)
        cases_time.plot(x='Last_Update', y='Deaths', linestyle='--', label='_nolegend_', color=color, ax=ax)

    legend = ax.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)

    plt.ylabel('people')

    if not args.nonlog:
        plt.yscale("log")

    plt.title('Confirmed Cases (—) and Deaths (---)')

    plt.grid(True)

    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
    parser.add_argument('--nonlog', default=False, action='store_true', help='set logarithmic scale for Y axis')
    parser.add_argument('--list', action='store_true', help='get list of available countries')
    parser.add_argument('--countries', type=str, nargs='+', default=['Russia'],
                        help='set list of countries to be plotted')

    args = parser.parse_args()

    cwd = os.getcwd()
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
        # open in-memory database
        connection = sqlite3.connect(':memory:')
        process(args, connection)
    except sqlite3.Error as e:
        print(e, file=sys.stderr)
    finally:
        if connection:
            connection.close()
