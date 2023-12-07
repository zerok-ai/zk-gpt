import pandas as pd
from prophet import Prophet
from prophet.plot import add_changepoints_to_plot
import numpy as np
from matplotlib import pyplot as plt

df = pd.read_csv("History of Save failures-data-2022-04-02 11_43_03.csv")
print("Input data")
print(df.head)
df.columns = ["ds", "y"]
# If you need to convert data
# df["ds"] =  pd.to_datetime(df["ds"],utc=False,unit='s')
# df['ds'] = pd.to_datetime(df.ds)
print(df.head)

prophet_instance = Prophet(changepoint_prior_scale=0.05, changepoint_range=1, interval_width=.95)
prophet_instance.fit(df)

# we are not concerned about predicting here, rather just fitting the data
future = prophet_instance.make_future_dataframe(periods=2, freq='2h')
print(" -- make_future_dataframe-- ")
print(future.tail())


forecast = prophet_instance.predict(future)
print(" -- model predict-- ")
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

fig = prophet_instance.plot(forecast)
fig.savefig('forecastwiki.png')

# Lets identify the points that are over the threshold

# find the dataframes having same indices
forecast_truncated_index = forecast.index.intersection(df.index)
forecast_truncated = forecast.loc[forecast_truncated_index]
print(forecast_truncated.shape[0],df.shape[0])

# Identify the thresholds
# indices =m.history[m.history['y'] > forecast_truncated['yhat_upper'] + buffer].index

# Identify the thresholds with some buffer
buffer = np.max(forecast_truncated['yhat_upper'])
print("Buffer=", buffer)
indices = prophet_instance.history[prophet_instance.history['y'] > buffer].index

# Get those points that have crossed the threshold
thresholded_df = prophet_instance.history.iloc[indices]  # ------> This has the threshold values and more important timestamp

figsize = (10, 6)
fig = plt.figure(facecolor='w', figsize=figsize)
ax = fig.add_subplot(111)
fig = prophet_instance.plot(forecast, ax=ax)

# plot the threhsolded points as red
ax.plot(thresholded_df['ds'].dt.to_pydatetime(), thresholded_df['y'], 'r.',
        label='Thresholded data points')
fig.savefig('forecastwiki_thresholded.png')