import os
import sys
import pandas as pd
import json


source_path = 'COVID-19/data'
cases_time_file = 'cases_time.csv'

data_base_path = 'data'
countries_params_file = 'countries_params.json'

countries_source = set(pd.read_csv(os.path.join(source_path, cases_time_file))['Country_Region'].unique())

with open(os.path.join(data_base_path, countries_params_file)) as f:
    countries_data_base = set(pd.DataFrame.from_dict(json.load(f), orient='index').index.unique())

print('countries_source - countries_data_base = ', countries_source - countries_data_base)
print()
print('countries_data_base - countries_source = ', countries_data_base - countries_source)
