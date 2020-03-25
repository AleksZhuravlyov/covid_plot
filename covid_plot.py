import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import sqlite3
import numpy as np
from scipy.optimize import curve_fit


def func(x, a, b, c, d):
    return (a * x + b) * np.exp(c + d / x)


def forecast(args, cases_time, ax, color):
    backward = np.timedelta64(args.forec[1], 'D')
    forward = np.timedelta64(args.forec[0], 'D')
    if not args.nonforec_deaths:
        deaths_lag = np.timedelta64(args.forec[2], 'D')

    # import time, confirmed cases and deaths form pandas to numpy
    time = cases_time.Last_Update.to_numpy()
    confirmed = cases_time.Confirmed.to_numpy()
    if not args.nonforec_deaths:
        deaths = cases_time.Deaths.to_numpy()

    # trim data for particular purposes of forecast
    date_init = time[0]
    date_current = time[-1]
    date_forward = date_current + forward
    date_backward_confirmed = date_current - backward
    if not args.nonforec_deaths:
        date_backward_deaths = date_current - backward + deaths_lag
    time_forecast_confirmed = np.arange(date_backward_confirmed, date_forward, dtype='datetime64[D]')
    if not args.nonforec_deaths:
        time_forecast_deaths = np.arange(date_backward_deaths, date_forward, dtype='datetime64[D]')
    ax.set_xlim(xmin=date_init, xmax=date_forward)

    # set time frame for curve fitting for confirmed cases
    backward_confirmed_condition = time > date_backward_confirmed
    time_confirmed = time[backward_confirmed_condition]
    confirmed = confirmed[backward_confirmed_condition]

    # set time frame for curve fitting for confirmed deaths
    if not args.nonforec_deaths:
        backward_deaths_condition = time > date_backward_deaths
        time_deaths = time[backward_deaths_condition]
        deaths = deaths[backward_deaths_condition]

    # employ numpy curve fitting for confirmed cases and deaths forecast
    confirmed_popt, confirmed_pcov = curve_fit(func, time_confirmed.astype('datetime64[D]').astype(int), confirmed,
                                               maxfev=int(1e+7))
    if not args.nonforec_deaths:
        deaths_popt, deaths_pcov = curve_fit(func, time_deaths.astype('datetime64[D]').astype(int), deaths,
                                             maxfev=int(1e+7))

    # plot forecast of confirmed cases and deaths
    ax.plot(time_forecast_confirmed.astype('datetime64[ns]'),
            func(time_forecast_confirmed.astype('datetime64[D]').astype(int), *confirmed_popt), linestyle='-',
            lw=1, color=color, label='_nolegend_')
    if not args.nonforec_deaths:
        ax.plot(time_forecast_deaths.astype('datetime64[ns]'),
                func(time_forecast_deaths.astype('datetime64[D]').astype(int), *deaths_popt), linestyle='--',
                lw=1, color=color, label='_nolegend_')


def process(args, connection):
    cases = pd.read_csv(os.path.join(base_path, cases_file_name))
    today = pd.read_csv(os.path.join(base_path, today_file_name))
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
    today.to_sql("today_cases", connection)

    fig, ax = plt.subplots()
    for country in countries:
        # plot country

        cases_time = pd.read_sql_query(
            f'SELECT Last_Update, Confirmed, Deaths from pandas_cases where Country_Region in (?) order by Last_Update ASC',
            connection, params=[country])
        cases_today = pd.read_sql_query(
            f'SELECT Last_Update, Confirmed, Deaths from today_cases where Country_Region in (?) order by Last_Update ASC',
            connection, params=[country])
        cases_time = cases_time.append(cases_today)
        color = next(ax._get_lines.prop_cycler)['color']
        cases_time['Last_Update'] = pd.to_datetime(cases_time['Last_Update'])  # .dt.normalize()
        cases_time.plot(x='Last_Update', y='Confirmed', linestyle='-', lw=2.1, color=color, ax=ax, label=country)
        cases_time.plot(x='Last_Update', y='Deaths', linestyle='--', lw=2.1, color=color, ax=ax, label='_nolegend_')

        if not args.nonforec:
            forecast(args, cases_time, ax, color)

    legend = ax.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)

    plt.ylabel('people')
    plt.xlabel('')
    ax.set_ylim(ymin=1)

    if not args.nonlog:
        plt.yscale('log')

    plt.title('Confirmed Cases (—) and Deaths (---)')

    plt.grid(True)

    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="CoViD-2019 daily plotting script")
    parser.add_argument('--nonlog', default=False, action='store_true', help='set linear scale for Y axis')
    parser.add_argument('--list', action='store_true', help='get list of available countries')
    parser.add_argument('--forec', type=str, nargs='+', default=['7', '20', '10'],
                        help='set forward, backward and deaths lag days for forecast')
    parser.add_argument('--nonforec', default=False, action='store_true', help='do not forecast at all')
    parser.add_argument('--nonforec_deaths', default=False, action='store_true', help='do not forecast deaths')
    parser.add_argument('--countries', type=str, nargs='+', default=['Russia'],
                        help='set list of countries to be plotted')

    args = parser.parse_args()

    cwd = os.getcwd()
    base_path = "COVID-19/data"
    cases_file_name = "cases_time.csv"
    today_file_name = "cases_country.csv"

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
