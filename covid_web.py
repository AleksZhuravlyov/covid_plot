#!/usr/bin/env python3
# coding: utf-8

import json
from datetime import datetime
from os import path
from types import SimpleNamespace
from flask import render_template, Blueprint
from flask import request
from process_procedures import process, preprocess
import hashlib

# basedir = '.'
basedir = '/var/www/html/covid/'
countries_file = path.join(basedir, 'data/countries_params.json')

covid_service = Blueprint('covid_service', __name__, template_folder='templates')

base_path = path.join(basedir, 'COVID-19/data')
cases_file = "cases_time.csv"
cases_today_file = "cases_country.csv"

with open(countries_file, 'r', encoding='utf-8') as f:
    countries_data = json.load(f)

all_countries = [el[0] for el in
                 sorted(countries_data.items(), key=lambda x: x[1]['country_ru'])]

w_pos = all_countries.index('World')
all_countries.insert(0, all_countries.pop(w_pos))

r_pos = all_countries.index('Russia')
all_countries.insert(1, all_countries.pop(r_pos))

d_pos = all_countries.index('Diamond Princess')
all_countries.insert(len(all_countries), all_countries.pop(d_pos))

d_pos = all_countries.index('MS Zaandam')
all_countries.insert(len(all_countries), all_countries.pop(d_pos))


@covid_service.route('/', methods=['GET', 'POST'])
def show_plot():
    chosen_countries = []
    log = True
    abs = False
    deaths = True
    current_day = False
    from_date = "2020-03-01"
    forec_confirmed = []
    forec_deaths = []
    if request.method == 'POST':
        chosen_countries = request.form.getlist('country')
        log = request.form.get('log')
        deaths = request.form.get('deaths')
        current_day = request.form.get('current_day')
        from_date = request.form.get('from_date')

        forec_confirmed_checked = request.form.get('forec-confirmed')
        forec_deaths_checked = request.form.get('forec-deaths')
        if forec_confirmed_checked:
            forec_confirmed_func = request.form.get('confirmed_function')
            forec_confirmed.append(forec_confirmed_func)
            forec_confirmed.append(request.form.get('for_period_confirmed'))
            forec_confirmed.append(request.form.get('on_period_confirmed'))

        if forec_deaths_checked:
            forec_deaths_func = request.form.get('deaths_function')
            forec_deaths.append(forec_deaths_func)
            forec_deaths.append(request.form.get('for_period_deaths'))
            forec_deaths.append(request.form.get('on_period_deaths'))

        nonlog = False
        if not log:
            nonlog = True

        nonabs = False
        if not abs:
            nonabs = True

        if set(chosen_countries) - set(all_countries):
            return render_template("covid.html", error="Выберите страны из списка!",
                                   countries=all_countries, countries_data=countries_data)
        args = SimpleNamespace(deaths=deaths, list=False, current_day=current_day,
                               from_date=from_date, nonlog=nonlog,
                               regions=chosen_countries,
                               forec_confirmed=forec_confirmed, forec_deaths=forec_deaths,
                               forec_current_day=[], nonabs=nonabs)
        cases, cases_today = preprocess(args, base_path, cases_file, cases_today_file)

        # Creating unique filename for the plot
        params = '_'.join([str(getattr(args, i)) for i in vars(args)])
        params = params + datetime.now().strftime('%Y-%m-%d-%H')
        m = hashlib.md5()
        name = params.encode('ascii', 'backslashreplace')
        m.update(name)
        fname = m.hexdigest()
        out_image = fname + '.png'

        imagepath = path.join(basedir, 'data', out_image)
        if not path.isfile(imagepath):
            _ = process(args, cases, cases_today, countries_data,
                        plot_file_name=imagepath, use_agg=True)
        return render_template("covid.html", image=out_image, countries=all_countries,
                               countries_data=countries_data,
                               chosen_countries=chosen_countries,
                               log=log, deaths=deaths, current_day=current_day,
                               from_date=from_date,
                               forec_confirmed=forec_confirmed, forec_deaths=forec_deaths)
    else:
        return render_template("covid.html", countries=all_countries,
                               countries_data=countries_data,
                               chosen_countries=chosen_countries, log=log, deaths=deaths,
                               current_day=current_day, from_date=from_date,
                               forec_confirmed=forec_confirmed, forec_deaths=forec_deaths)
