import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import sqlite3
import numpy as np
from scipy.optimize import curve_fit
import datetime


def func_linear(x, a, b):
    return a * x + b


def func_poly(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d


def func_covid(x, a, b, c, d):
    return (a * x + b) * np.exp(c / x + d)


def forecast(func_type, forward, backward, cases_time, field_name, ax, color, last_day):
    # set function type for curve fitting
    if func_type == 'linear':
        func = func_linear
    elif func_type == 'poly':
        func = func_poly
    elif func_type == 'covid':
        func = func_covid
    else:
        print("No such function type, use exp or poly", file=sys.stderr)
        sys.exit(-1)

    # import time, confirmed cases and deaths form pandas to numpy
    time = cases_time.Last_Update.to_numpy()
    value = cases_time[field_name].to_numpy()

    # trim data for particular purposes of forecast
    date_current = time[-1]
    date_forward = date_current + forward
    date_backward = date_current - backward

    time_forecast = np.arange(date_backward, date_forward, dtype='datetime64[D]')
    ax.set_xlim(xmax=date_forward)

    # set time frame for curve fitting for confirmed cases
    backward_condition = time > date_backward
    if not last_day:
        backward_condition[-1] = False  # the last day is not use since can be non filled
    time_fitting = time[backward_condition]
    value = value[backward_condition]

    # employ numpy curve fitting for forecast
    popt, pcov = curve_fit(func, time_fitting.astype('datetime64[D]').astype(float), value, maxfev=int(1.e+9))

    # plot forecast
    forecast_value = pd.DataFrame()
    forecast_value['Last_Update'] = time_forecast.astype('datetime64[ns]')
    forecast_value[field_name] = func(time_forecast.astype('datetime64[D]').astype(int), *popt)
    forecast_value['Last_Update'] = forecast_value['Last_Update'].dt.normalize()

    linestyle = '-'
    if field_name == 'Deaths':
        linestyle = '--'

    forecast_value.plot(x='Last_Update', y=field_name, linestyle=linestyle, lw=1, color=color, ax=ax, label='')

    return date_forward


def process(args, connection, base_path, cases_file, today_file):
    cases = pd.read_csv(os.path.join(base_path, cases_file))
    today = pd.read_csv(os.path.join(base_path, today_file))
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

    if args.total:
        cases_all = pd.read_sql_query(
            f'SELECT Last_Update, Sum(Confirmed) as Confirmed, Sum(Deaths) as Deaths from pandas_cases \
             group by Last_Update order by Last_Update ASC',
            connection)
        cases_all = cases_all.append(
            pd.read_sql_query(
            f'SELECT Last_Update, Sum(Confirmed) as Confirmed, Sum(Deaths) as Deaths from today_cases \
              group by CAST(Last_Update AS DATE) order by CAST(Last_Update AS DATE) ASC',
            connection))

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
        cases_time['Last_Update'] = pd.to_datetime(cases_time['Last_Update']).dt.normalize()
        cases_time.plot(x='Last_Update', y='Confirmed', linestyle='-', lw=2.1, color=color, ax=ax, label=country)
        cases_time.plot(x='Last_Update', y='Deaths', linestyle='--', lw=2.1, color=color, ax=ax, label='')

        # forecast and plot confirmed cases
        if args.forec_confirmed:
            date_forecast_confirmed = forecast(func_type=args.forec_confirmed[0],
                                               forward=np.timedelta64(int(args.forec_confirmed[1]), 'D'),
                                               backward=np.timedelta64(int(args.forec_confirmed[2]), 'D'),
                                               cases_time=cases_time, field_name='Confirmed', ax=ax, color=color,
                                               last_day=args.last_day)

        # forecast and plot deaths
        if args.forec_deaths:
            date_forecast_deaths = forecast(func_type=args.forec_deaths[0],
                                            forward=np.timedelta64(int(args.forec_deaths[1]), 'D'),
                                            backward=np.timedelta64(int(args.forec_deaths[2]), 'D'),
                                            cases_time=cases_time, field_name='Deaths', ax=ax, color=color,
                                            last_day=args.last_day)

    if args.total:
        color = next(ax._get_lines.prop_cycler)['color']
        cases_all['Last_Update'] = pd.to_datetime(cases_all['Last_Update']).dt.normalize()
        cases_all.plot(x='Last_Update', y='Confirmed', linestyle='-', lw=2.1, color=color, ax=ax, label='World')
        cases_all.plot(x='Last_Update', y='Deaths', linestyle='--', lw=2.1, color=color, ax=ax, label='')

    legend = ax.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)

    plt.ylabel('people')
    plt.xlabel('')
    ax.set_ylim(ymin=1)
    if args.from_date:
        ax.set_xlim(xmin=args.from_date)
    if args.forec_confirmed and args.forec_deaths:
        if date_forecast_confirmed > date_forecast_deaths:
            ax.set_xlim(xmax=date_forecast_confirmed)
        else:
            ax.set_xlim(xmax=date_forecast_deaths)

    if not args.nonlog:
        plt.yscale('log')

    plt.title('Confirmed Cases (—) and Deaths (---)')

    plt.grid(True)

    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='COVID-19 disease daily plotting script',
                                     epilog='Forecast works mostly under manual control, but works and\
                                     the corresponding fitting functions are as follows: linear=a*x+b,\
                                     poly=a*x^3+b*x^2+c*x+d and covid=(a*x+b)*exp(c/x+d).', prog='covid_plot')

    parser.add_argument('--nonlog', default=False, action='store_true', help='set linear scale for Y axis')
    parser.add_argument('--list', action='store_true', help='get list of available countries')
    parser.add_argument('--last_day', default=False, action='store_true', help='use the last day for forecast')
    parser.add_argument('--forec_confirmed', type=str, nargs='+', default=[],
                        help='set function type (linear, poly or covid), forward and backward days for forecast\
                        confirmed cases: type n n')
    parser.add_argument('--forec_deaths', type=str, nargs='+', default=[],
                        help='set function type (linear, poly or covid), forward and backward days for forecast\
                        deaths: type n n')
    parser.add_argument('--countries', type=str, nargs='+', default=['Russia'],
                        help='set list of countries to be plotted')
    parser.add_argument("--from_date", type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                        help='set init data for plot: Y-m-d')
    parser.add_argument('--total', default=False, action='store_true', help='Plot sum over all countries.')

    args = parser.parse_args()

    cwd = os.getcwd()
    base_path = "COVID-19/data"
    cases_file = "cases_time.csv"
    today_file = "cases_country.csv"

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
        process(args, connection, base_path, cases_file, today_file)
    except sqlite3.Error as e:
        print(e, file=sys.stderr)
    finally:
        if connection:
            connection.close()
