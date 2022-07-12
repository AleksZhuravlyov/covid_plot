import argparse
import datetime
import os
from os import path
import json

from process_procedures import process, preprocess

parser = argparse.ArgumentParser(description='COVID-19 disease daily plotting script',
                                 epilog='Forecast works mostly under manual control, but works '
                                        'and the corresponding fitting approaches are '
                                        'as follows: '
                                        'linear=a*x+b, poly=a*x^3+b*x^2+c*x+d, '
                                        'covid=(a*x+b)*exp(c/x+d), '
                                        'cnn is preconfigured convolutional neural network, while '
                                        'ldm is preconfigured linear model with dense layer',
                                 prog='covid_plot')

parser.add_argument('--nonlog', default=False, action='store_true',
                    help='set linear scale for Y axis')
parser.add_argument('--list', action='store_true',
                    help='get list of available regions')
parser.add_argument('--forec_current_day', default=False, action='store_true',
                    help='use the current day for forecast')
parser.add_argument('--current_day', default=False, action='store_true',
                    help='use the current day for visualisation')
parser.add_argument('--deaths', default=False, action='store_true',
                    help='show deaths')
parser.add_argument('--forec_confirmed', type=str, nargs='+', default=[],
                    help='set function type (linear, poly, covid, cnn or ldm), '
                         'forward and backward days for forecast confirmed cases: type n n')
parser.add_argument('--forec_deaths', type=str, nargs='+', default=[],
                    help='set function type (linear, poly, covid, cnn or ldm), '
                         'forward and backward days for forecast deaths: type n n')
parser.add_argument('--regions', type=str, nargs='+', default=['Russia'],
                    help='set list of regions to be plotted')
parser.add_argument("--from_date",
                    type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),
                    default=None, help='set init data for plot: Y-m-d')
parser.add_argument('--nonabs', default=False, action='store_true',
                    help='set number of people as fraction of population')
parser.add_argument('--daily', default=False, action='store_true',
                    help='show daily data')

args = parser.parse_args()

cwd = os.getcwd()
covid_data_path = "COVID-19/data"
cases_file = "cases_time.csv"
cases_today_file = "cases_country.csv"

countries_params_path = '.'
countries_params_file = path.join(countries_params_path, 'data/countries_params.json')
with open(countries_params_file, 'r', encoding='utf-8') as f:
    countries_params = json.load(f)

if os.path.isdir(covid_data_path):
    os.chdir(covid_data_path)
    os.system("git pull")
    os.chdir(cwd)
else:
    os.system("git clone https://github.com/CSSEGISandData/COVID-19")
    os.chdir('COVID-19')
    os.system("git checkout web-data")
    os.chdir("..")

cases, cases_today = preprocess(args, covid_data_path, cases_file, cases_today_file)
process(args, cases, cases_today, countries_params)
