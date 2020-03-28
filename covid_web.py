#!/usr/bin/env python3
# coding: utf-8

import sys
from os import path
from flask import render_template, Blueprint
from flask import request
from covid_plot import process, preprocess
from types import SimpleNamespace
from datetime import datetime
import json

basedir = '/var/www/html/covid/'
countries_file = path.join(basedir, 'data/countries.json')

covid_service = Blueprint('covid_service', __name__, template_folder='templates')

base_path = path.join(basedir, 'COVID-19/data')
cases_file = "cases_time.csv"
cases_today_file = "cases_country.csv"

with open(countries_file, 'r') as f:
    all_countries = json.load(f)

@covid_service.route('/', methods=['GET', 'POST'])
def show_plot():
    if request.method == 'POST':
        chosen_countries = request.form.getlist('country')
        log = request.form.get('log')
        nonlog = False
        if not log:
            nonlog = True
        params = SimpleNamespace(deaths=True, list=False, from_date=None, nonlog=nonlog, regions=chosen_countries, forec_confirmed=[], forec_deaths=[])
        cases = preprocess(params, base_path, cases_file, cases_today_file)
        out_image = '_'.join(['_'.join(chosen_countries), datetime.now().strftime('%Y-%m-%d-%H-%M-%S')]) + '.png'
        _ = process(params, cases, save='/var/www/html/covid/data/'+out_image)
        return render_template("covid.html", image=out_image, countries=all_countries)
    else:
        return render_template("covid.html", countries=all_countries)
