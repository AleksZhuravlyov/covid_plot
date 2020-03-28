import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import numpy as np
from scipy.optimize import curve_fit
import datetime


def func_linear(x, a, b):
    return a * x + b


def func_poly(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d


def func_covid(x, a, b, c, d):
    return (a * x + b) * np.exp(c / x + d)


def forecast(forec_args, cases, field_name, ax, color, last_day):
    # set function type for curve fitting

    func_type = forec_args[0]
    if func_type == 'linear':
        func = func_linear
    elif func_type == 'poly':
        func = func_poly
    elif func_type == 'covid':
        func = func_covid
    else:
        print('No such function type, use covid, poly or linear', file=sys.stderr)
        sys.exit(-1)

    forward = np.timedelta64(int(forec_args[1]), 'D')
    backward = np.timedelta64(int(forec_args[2]), 'D')

    # import time, confirmed cases and deaths form pandas to numpy
    date = cases.Date.to_numpy()
    value = cases[field_name].to_numpy()

    # trim data for particular purposes of forecast
    date_current = date[-1]
    date_forward = date_current + forward
    date_backward = date_current - backward

    date_range_forecast = np.arange(date_backward, date_forward, dtype='datetime64[D]')
    ax.set_xlim(xmax=date_forward)

    # set time frame for curve fitting for confirmed cases
    backward_condition = date > date_backward
    if not last_day:
        backward_condition[-1] = False  # the last day is not use since can be non filled
    date_range_fitting = date[backward_condition]
    value = value[backward_condition]

    # employ numpy curve fitting for forecast
    popt, pcov = curve_fit(func, date_range_fitting.astype('datetime64[D]').astype(float), value, maxfev=int(1.e+9))

    # plot forecast
    forecast_value = pd.DataFrame()
    forecast_value['Date'] = date_range_forecast.astype('datetime64[ns]')
    forecast_value[field_name] = func(date_range_forecast.astype('datetime64[D]').astype(int), *popt)
    forecast_value.Date = forecast_value.Date.dt.normalize()

    linestyle = '-'
    if field_name == 'Deaths':
        linestyle = '--'

    forecast_value.plot(x='Date', y=field_name, linestyle=linestyle, lw=1, color=color, ax=ax, label='')

    if np.datetime64(int(ax.get_xlim()[1]), 'D') < date_forward:
        ax.set_xlim(xmax=date_forward)


def preprocess(args, base_path, cases_file, cases_today_file):
    rename_dict = {'Country_Region': 'Region', 'Last_Update': 'Date'}
    drop_list_cases_today = ['Lat', 'Long_', 'Active', 'Recovered']
    drop_list_cases = ['Active', 'Delta_Confirmed', 'Delta_Recovered']

    cases_today = pd.read_csv(os.path.join(base_path, cases_today_file))
    cases_today.rename(columns=rename_dict, inplace=True)
    cases_today = cases_today.drop(columns=drop_list_cases_today)
    cases_today['Date'] = pd.to_datetime(cases_today['Date']) - np.timedelta64(1, 'D')

    cases = pd.read_csv(os.path.join(base_path, cases_file))
    cases.rename(columns=rename_dict, inplace=True)
    cases = cases.drop(columns=drop_list_cases)
    cases['Date'] = pd.to_datetime(cases['Date']).dt.normalize()
    cases = cases.append(cases_today, ignore_index=True, sort=True)
    cases = cases.sort_values(by=['Region', 'Date'])

    if 'World' in set(args.regions):
        world = cases.groupby(['Date']).sum()
        world['Region'] = 'World'
        world['Date'] = world.index
        cases = cases.append(world, ignore_index=True, sort=True)

    return cases


def process(args, cases):
    regions_all = sorted(set(cases['Region'].values.tolist()))
    regions = sorted(list(set(regions_all) & set(args.regions)))

    if len(regions) == 0:
        print("No known regions were specified. Should be in ", file=sys.stderr)
        print(regions_all, file=sys.stderr)
        sys.exit(-1)

    if args.list:
        print(['World'])
        print(regions_all)
        sys.exit(0)

    fig, ax = plt.subplots()
    for region in regions:
        # plot region

        color = next(ax._get_lines.prop_cycler)['color']

        cases[cases['Region'] == region].plot(x='Date', y='Confirmed',
                                              linestyle='-', lw=2.1, color=color, ax=ax, label=region)
        if args.deaths or args.forec_deaths:
            cases[cases['Region'] == region].plot(x='Date', y='Deaths',
                                                  linestyle='--', lw=2.1, color=color, ax=ax, label='')

        # forecast and plot confirmed cases
        if args.forec_confirmed:
            forecast(args.forec_confirmed, cases[cases['Region'] == region],
                     field_name='Confirmed', ax=ax, color=color, last_day=args.last_day)

        # forecast and plot deaths
        if args.forec_deaths:
            forecast(args.forec_deaths, cases[cases['Region'] == region],
                     field_name='Deaths', ax=ax, color=color, last_day=args.last_day)

    legend = ax.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)

    plt.ylabel('people')
    plt.xlabel('')
    ax.set_ylim(ymin=1)
    if args.from_date:
        ax.set_xlim(xmin=args.from_date)

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
    parser.add_argument('--list', action='store_true', help='get list of available regions')
    parser.add_argument('--last_day', default=False, action='store_true', help='use the last day for forecast')
    parser.add_argument('--deaths', default=False, action='store_true', help='show deaths')
    parser.add_argument('--forec_confirmed', type=str, nargs='+', default=[],
                        help='set function type (linear, poly or covid), forward and backward days for forecast\
                        confirmed cases: type n n')
    parser.add_argument('--forec_deaths', type=str, nargs='+', default=[],
                        help='set function type (linear, poly or covid), forward and backward days for forecast\
                        deaths: type n n')
    parser.add_argument('--regions', type=str, nargs='+', default=['Russia'],
                        help='set list of regions to be plotted')
    parser.add_argument("--from_date", type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), default=None,
                        help='set init data for plot: Y-m-d')

    args = parser.parse_args()

    cwd = os.getcwd()
    base_path = "COVID-19/data"
    cases_file = "cases_time.csv"
    cases_today_file = "cases_country.csv"

    if os.path.isdir(base_path):
        os.chdir(base_path)
        os.system("git pull")
        os.chdir(cwd)
    else:
        os.system("git clone https://github.com/CSSEGISandData/COVID-19")
        os.chdir('COVID-19')
        os.system("git checkout web-data")
        os.chdir("..")

    cases = preprocess(args, base_path, cases_file, cases_today_file)
    process(args, cases)
