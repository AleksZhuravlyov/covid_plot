import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ldm_forecast_methods import fit_model

df = pd.read_csv('cases_tmp.csv')
places = df.Place.unique()
place = places[0]
df = df[df.Place == place]

Confirmed_current = df.loc[df.Date == df.Date.max()]['Confirmed'].values[0]
Deaths_current = df.loc[df.Date == df.Date.max()]['Deaths'].values[0]
df.drop(df[df.Confirmed < 10000].index, inplace=True)
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

IN_STEPS = 42
OUT_STEPS = 14
model, window = fit_model(train_df, val_df, test_df, IN_STEPS, OUT_STEPS)

window.plot(model)
plt.show()

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

df = df * std + mean
fig, ax1 = plt.subplots()
df.plot(ax=ax1)
prediction_df.plot(y=['Confirmed_daily', 'Deaths_daily'], ax=ax1)
ax1.set_xlim(xmin='2021-05-10')
plt.show()
