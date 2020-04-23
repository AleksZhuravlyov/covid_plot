#!/usr/bin/env python3
# coding: utf-8

import json
from datetime import datetime
from os import path
from types import SimpleNamespace
from flask import render_template, Blueprint
from flask import request
from covid_plot import process, preprocess
import hashlib


# basedir = '.'
basedir = '/var/www/html/covid/'
countries_file = path.join(basedir, 'data/countries.json')

covid_service = Blueprint('covid_service', __name__, template_folder='templates')

base_path = path.join(basedir, 'COVID-19/data')
cases_file = "cases_time.csv"
cases_today_file = "cases_country.csv"

with open(countries_file, 'r') as f:
    all_countries = json.load(f)

all_countries = sorted(all_countries)
w_pos = all_countries.index('World')
all_countries.insert(0, all_countries.pop(w_pos))


@covid_service.route('/', methods=['GET', 'POST'])
def show_plot():
    chosen_countries = []
    log = True
    deaths = True
    current_day = False
    from_date = "2020-03-01"
    forec_confirmed = list()
    if request.method == 'POST':
        chosen_countries = request.form.getlist('country')
        log = request.form.get('log')
        deaths = request.form.get('deaths')
        current_day = request.form.get('current_day')
        from_date = request.form.get('from_date')             
        
        forec_confirmed_func = request.form.get('confirmed_function')        
        if forec_confirmed_func != '':            
            forec_confirmed.append(forec_confirmed_func)
            forec_confirmed.append(request.form.get('for_period_confirmed'))
            forec_confirmed.append(request.form.get('on_period_confirmed'))        
        
        nonlog = False
        if not log:
            nonlog = True
        pass
        if set(chosen_countries) - set(all_countries):
            return render_template("covid.html", error="Выберите страны из списка!",
                                   countries=all_countries)
        args = SimpleNamespace(deaths=deaths, list=False, current_day=current_day,
                               from_date=from_date, nonlog=nonlog, regions=chosen_countries,
                               forec_confirmed=forec_confirmed, forec_deaths=[],
                               forec_current_day=[])
        cases = preprocess(args, base_path, cases_file, cases_today_file)

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
            _ = process(args, cases, plot_file_name=imagepath, use_agg=True)
        return render_template("covid.html", image=out_image, countries=all_countries,
                               chosen_countries=chosen_countries, log=log, deaths=deaths,
                               current_day=current_day, from_date=from_date,
                               forec_confirmed=forec_confirmed)
    else:
        return render_template("covid.html", countries=all_countries,
                               chosen_countries=chosen_countries, log=log, deaths=deaths,
                               current_day=current_day, from_date=from_date,
                               forec_confirmed=forec_confirmed)
