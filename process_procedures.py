import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import cnn_forecast_methods  as cnn
import ldm_forecast_methods as ldm


def func_linear(x, a, b):
    return a * x + b


def func_poly(x, a, b, c, d):
    return a * x ** 3 + b * x ** 2 + c * x + d


def func_covid(x, a, b, c, d):
    return (a * x + b) * np.exp(c / x + d)


def forecast(forec_args, cases, field_name, ax, color, forec_current_day, isDaily, nonabs, population):
    # set function type for curve fitting

    func_type = forec_args[0]
    if func_type == 'linear':
        func = func_linear
    elif func_type == 'poly':
        func = func_poly
    elif func_type == 'covid':
        func = func_covid
    elif func_type != 'cnn' and func_type != 'ldm':
        print('No such function type, use covid, poly or linear', file=sys.stderr)
        sys.exit(-1)

    lw = 1.05
    marker = 'o'
    markersize = 1.35
    linestyle = '-'
    if field_name == 'Deaths':
        linestyle = '--'
        lw = 1.05
        marker = 2.
        markersize = 1.75

    if func_type != 'cnn' and func_type != 'ldm':
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
                               value, maxfev=int(1.e+9))

        # plot forecast
        forecast_value = pd.DataFrame()
        forecast_value['Date'] = date_range_forecast.astype('datetime64[ns]')
        forecast_value[field_name] = func(
            date_range_forecast.astype('datetime64[D]').astype(int), *popt)
        forecast_value.Date = forecast_value.Date.dt.normalize()

        forecast_value.plot(x='Date', y=field_name, linestyle=linestyle, lw=lw, color=color,
                            ax=ax, label='', marker=marker, markersize=markersize)

        if np.datetime64(int(ax.get_xlim()[1]), 'D') < date_forward:
            ax.set_xlim(xmax=date_forward)
    else:
        df = cases.copy(deep=True)
        if not forec_current_day:
            df.drop(df[df.Date == df.Date.max()].index, inplace=True)

        Confirmed_current = df.loc[df.Date == df.Date.max()]['Confirmed'].values[0]
        Deaths_current = df.loc[df.Date == df.Date.max()]['Deaths'].values[0]
        if nonabs:
            Confirmed_current *= population
            Deaths_current *= population

        limit = 10000.
        if nonabs:
            limit /= population

        df.drop(df[df.Confirmed < limit].index, inplace=True)
        df.drop(columns=['Place', 'Confirmed', 'Deaths'], inplace=True)
        date_time = pd.to_datetime(df.pop('Date'), format='%Y.%m.%d')

        train_df = df[0:int(len(df) * 0.7)]
        val_df = df[int(len(df) * 0.7):int(len(df) * 0.9)]
        test_df = df[int(len(df) * 0.9):]
        mean = train_df.mean()
        std = train_df.std()
        df = (df - mean) / std
        train_df = (train_df - mean) / std
        val_df = (val_df - mean) / std
        test_df = (test_df - mean) / std

        IN_STEPS = int(forec_args[2])
        OUT_STEPS = int(forec_args[1])
        
        if func_type == 'cnn':
            model, window = cnn.fit_model(train_df, val_df, test_df, IN_STEPS, OUT_STEPS)
        elif func_type == 'ldm':
            model, window = ldm.fit_model(train_df, val_df, test_df, IN_STEPS, OUT_STEPS)

        prediction = model(np.array([df[- OUT_STEPS:]]))
        prediction_df = pd.DataFrame(prediction.numpy()[0])
        prediction_df.columns = df.columns
        df.index = date_time
        time_max = date_time[-OUT_STEPS:].max()
        prediction_time = pd.date_range(time_max, periods=OUT_STEPS + 1, freq="D")
        prediction_time = prediction_time.drop(time_max)
        prediction_df.index = prediction_time
        prediction_df = prediction_df * std + mean
        prediction_df['Confirmed'] = prediction_df['Confirmed_daily'].cumsum() + Confirmed_current
        prediction_df['Deaths'] = prediction_df['Deaths_daily'].cumsum() + Deaths_current
        if nonabs:
            prediction_df['Confirmed'] /= population
            prediction_df['Deaths'] /= population

        prediction_df.plot(y=field_name, linestyle=linestyle, lw=lw, color=color,
                           ax=ax, label='', marker=marker, markersize=markersize)

        if isDaily and field_name == 'Confirmed':
            prediction_df.plot(y=field_name + '_daily', secondary_y=True, linestyle='-', lw=0.15, color=color,
                               ax=ax, label='', marker='s', markersize=2)


def preprocess(args, covid_data_path, cases_file, cases_today_file):
    useful_columns = ['Country_Region', 'Last_Update', 'Confirmed', 'Deaths']
    rename_dict = {'Country_Region': 'Place', 'Last_Update': 'Date'}

    cases_raw = pd.read_csv(os.path.join(covid_data_path, cases_file), low_memory=False)

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

    # cases.to_csv('cases_tmp.csv', index=False)

    populations = {}
    for region in regions:
        populations[region] = countries_params[region]['population']
    if args.nonabs:
        for region in regions:
            cases.loc[cases['Place'] == region, ['Confirmed', 'Deaths']] = \
                cases.loc[cases['Place'] == region, ['Confirmed', 'Deaths']] / populations[region]

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
                     forec_current_day=args.forec_current_day, isDaily=args.daily,
                     nonabs=args.nonabs, population=populations[region])

        # forecast and plot deaths
        if args.forec_deaths:
            forecast(args.forec_deaths, cases[cases['Place'] == region],
                     field_name='Deaths', ax=ax1, color=color,
                     forec_current_day=args.forec_current_day, isDaily=args.daily,
                     nonabs=args.nonabs, population=populations[region])

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
