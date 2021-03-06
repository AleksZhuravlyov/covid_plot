import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


def func_linear(x, a, b):
    return a * x + b


def func_poly(x, a, b, c, d):
    return a * x ** 3 + b * x ** 2 + c * x + d


def func_covid(x, a, b, c, d):
    return (a * x + b) * np.exp(c / x + d)


def forecast(forec_args, cases, field_name, ax, color, forec_current_day):
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
    if not forec_current_day:
        backward_condition[-1] = False  # the last day is not use since can be non filled
    date_range_fitting = date[backward_condition]
    value = value[backward_condition]

    # employ numpy curve fitting for forecast
    popt, pcov = curve_fit(func, date_range_fitting.astype('datetime64[D]').astype(float),
                           value,
                           maxfev=int(1.e+9))

    # plot forecast
    forecast_value = pd.DataFrame()
    forecast_value['Date'] = date_range_forecast.astype('datetime64[ns]')
    forecast_value[field_name] = func(
        date_range_forecast.astype('datetime64[D]').astype(int),
        *popt)
    forecast_value.Date = forecast_value.Date.dt.normalize()

    linestyle = '-'
    if field_name == 'Deaths':
        linestyle = '--'

    forecast_value.plot(x='Date', y=field_name, linestyle=linestyle, lw=1, color=color,
                        ax=ax,
                        label='')

    if np.datetime64(int(ax.get_xlim()[1]), 'D') < date_forward:
        ax.set_xlim(xmax=date_forward)


def preprocess(args, covid_data_path, cases_file, cases_today_file):
    useful_columns = ['Country_Region', 'Last_Update', 'Confirmed', 'Deaths']
    rename_dict = {'Country_Region': 'Place', 'Last_Update': 'Date'}

    cases_raw = pd.read_csv(os.path.join(covid_data_path, cases_file))
    # remove USA states
    cases_raw = cases_raw[cases_raw['UID'] != 840]
    cases = pd.DataFrame(cases_raw[useful_columns])
    cases.rename(columns=rename_dict, inplace=True)
    cases['Date'] = pd.to_datetime(cases['Date']).dt.normalize()
    cases = cases.groupby(['Date', 'Place']).sum().reset_index()
    cases = cases.sort_values(by=['Place', 'Date'])

    cases_today_raw = pd.read_csv(os.path.join(covid_data_path, cases_today_file))
    # remove USA states
    cases_today_raw = cases_today_raw[cases_today_raw['UID'] != 840]
    cases_today = pd.DataFrame(cases_today_raw[useful_columns])
    cases_today.rename(columns=rename_dict, inplace=True)
    cases_today['Date'] = pd.to_datetime(cases_today['Date']) - np.timedelta64(1, 'D')
    cases_today = cases_today.groupby(['Date', 'Place']).sum().reset_index()
    cases_today = cases_today.sort_values(by=['Place', 'Date'])

    return cases, cases_today


def process(args, cases, cases_today, countries_params,
            plot_file_name=False, use_agg=False):
    if 'World' in set(args.regions):
        world = cases.groupby(['Date']).sum()
        world['Place'] = 'World'
        world['Date'] = world.index
        cases = cases.append(world, ignore_index=True, sort=True)

    regions_all = sorted(set(cases['Place'].values.tolist()))
    regions = sorted(list(set(regions_all) & set(args.regions)))

    if len(regions) == 0:
        print('No known regions were specified. Should be in ', file=sys.stderr)
        print(regions_all, file=sys.stderr)
        sys.exit(-1)

    if args.list:
        print(['World'])
        print(regions_all)
        sys.exit(0)

    if args.current_day or args.forec_current_day:
        cases = cases.append(cases_today, ignore_index=True, sort=True)

    # drop places which are not selected
    cases = pd.DataFrame(cases[cases['Place'].isin(regions)])

    for region in regions:
        cases.loc[cases['Place'] == region, 'Confirmed_daily'] = \
            cases.loc[cases['Place'] == region, 'Confirmed'].diff()
        cases.loc[cases['Place'] == region, 'Deaths_daily'] = \
            cases.loc[cases['Place'] == region, 'Deaths'].diff()

    cases['Confirmed_daily'].fillna(cases['Confirmed'], inplace=True)
    cases['Deaths_daily'].fillna(cases['Deaths'], inplace=True)

    if args.nonabs:
        for region in regions:
            population = countries_params[region]['population']
            cases.loc[cases['Place'] == region, ['Confirmed', 'Deaths']] = \
                cases.loc[cases['Place'] == region, ['Confirmed', 'Deaths']] / population

    print(cases)

    if use_agg:
        plt.switch_backend('Agg')

    fig, ax1 = plt.subplots()
    plt.title('Подтвержденные (—)')
    if args.daily:
        plt.title(ax1.get_title() + ' и новые (▪)')
    plt.title(ax1.get_title() + ' случаи')
    if args.deaths or args.forec_deaths:
        plt.title(ax1.get_title() + ', смерти (---)')

    for region in regions:
        # plot region

        color = next(ax1._get_lines.prop_cycler)['color']

        cases[cases['Place'] == region].plot(x='Date', y='Confirmed', linestyle='-',
                                             lw=2.1,
                                             color=color, ax=ax1, marker='o',
                                             markersize=2.7,
                                             label=countries_params[region]['country_ru'])

        if args.daily:
            ax2 = cases[cases['Place'] == region].plot(x='Date', y='Confirmed_daily',
                                                       linestyle='-',
                                                       secondary_y=True,
                                                       lw=0.3,
                                                       color=color, ax=ax1, marker='s',
                                                       markersize=4)

        if args.deaths or args.forec_deaths:
            cases[cases['Place'] == region].plot(x='Date', y='Deaths',
                                                 linestyle='--', lw=2.1, color=color,
                                                 ax=ax1, label='', marker=2,
                                                 markersize=3.5)

        # forecast and plot confirmed cases
        if args.forec_confirmed:
            forecast(args.forec_confirmed, cases[cases['Place'] == region],
                     field_name='Confirmed', ax=ax1, color=color,
                     forec_current_day=args.forec_current_day)

        # forecast and plot deaths
        if args.forec_deaths:
            forecast(args.forec_deaths, cases[cases['Place'] == region],
                     field_name='Deaths', ax=ax1, color=color,
                     forec_current_day=args.forec_current_day)

    legend = ax1.legend()
    for handle in legend.legendHandles:
        handle.set_linewidth(5.0)

    if args.nonabs:
        ax1.set_ylabel('Всего (доля населения)')
    else:
        ax1.set_ylabel('Всего (человек)')

    if args.daily:
        ax2.set_ylabel('Новые случаи (человек)')

    plt.xlabel('')
    if args.from_date:
        ax1.set_xlim(xmin=args.from_date)

    if not args.nonlog:
        ax1.set_yscale('log')

    plt.grid(True)

    if plot_file_name:
        plt.savefig(plot_file_name, dpi=150, bbox_inches='tight')
    else:
        plt.show()

    plt.close()
