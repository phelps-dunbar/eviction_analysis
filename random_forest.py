# This script is for building a model predicting the worked dollars
# for all potential eiction analysis clients

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


# read in the data
df = pd.read_csv('test.csv')
print(df.head())

# drop all columns starting with "client_address"
for col in df.columns:
    if col.startswith('client_address'):
        df.drop(col, axis=1, inplace=True)

# drop the matter description columns
df = df.drop(['matter_description'], axis=1)

# generate the matter open year from the matter open date
# and drop the matter open date column
df['matter_open_year'] = pd.DatetimeIndex(df['matter_open_date']).year
df = df.drop(['matter_open_date'], axis=1)

# sum up the worked_dollars by matter_id
df_worked_dollars = df[['matter_id', 'worked_dollars']].groupby([
                                                                'matter_id']).sum()

# sum up the worked_hours by matter_id
df_worked_hours = df[['matter_id', 'worked_hours']
                     ].groupby(['matter_id']).sum()

# calculate the weighted average worked_rate by matter_id
df_worked_rate = df[['matter_id', 'worked_rate', 'worked_hours']].groupby(
    ['matter_id']).apply(lambda x: np.average(x['worked_rate'], weights=x['worked_hours'])).rename('worked_rate')

# calculate the unbilled hours by matter_id by using total_worked_hours - total_billed_hours
df['unbilled_hours'] = df_worked_hours['worked_hours'] - df['billed_hours']
df_unbilled_hours = df[['matter_id', 'unbilled_hours']].groupby(
    ['matter_id']).sum()

# drop the worked_hours, worked_rate, billed_hours, and billed_rate
# and billed_dollars columns
df = df.drop(['worked_hours', 'worked_rate', 'billed_hours',
             'billed_rate', 'billed_dollars'], axis=1)


# drop the worked_dollars column
df = df.drop(['worked_dollars'], axis=1)
# attach the total_worked_dollars column to the df dataframe
df = df.merge(df_worked_dollars, how='left', on='matter_id')
# df = df.merge(df_worked_hours, how='left', on='matter_id')
# df = df.merge(df_worked_rate, how='left', on='matter_id')
# df = df.merge(df_unbilled_hours, how='left', on='matter_id')

# generate the number of timekeeper worked for each matter_id
df_timekeeper = df[['matter_id', 'timekeeper']].groupby(
    ['matter_id']).nunique()
# drop the timekeeper_id column
df = df.drop(['timekeeper'], axis=1)
# attach the timekeeper_count column to the df dataframe
df = df.merge(df_timekeeper, how='left', on='matter_id')
df.to_csv('WIP_data.csv')

# drop the matter_id, client_name, and practice_code columns
df = df.drop(['matter_id', 'client_name', 'practice_code'],
             axis=1).drop_duplicates()

print(df.head())
# one-hot encode the categorical columns:state, location, department
df = pd.get_dummies(df, columns=['state', 'location', 'department'])

print(df.columns)

# now start building the model
# split the data into training and test sets
X = df.drop(['worked_dollars'], axis=1)
y = df['worked_dollars']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# build the model
rf = RandomForestRegressor(n_estimators=100, max_depth=10,
                           min_samples_leaf=10, random_state=0)
rf.fit(X_train, y_train)

# predict the test set
y_pred = rf.predict(X_test)

# show the R-squared
r2 = rf.score(X_test, y_test)
print(f'R-squared: {r2}')

# calculate the mean squared error
mse = mean_squared_error(y_test, y_pred)
print(f'MSE: {mse}')

# calculate the root mean squared error
rmse = np.sqrt(mse)
print(f'RMSE: {rmse}')

# show the feature importance
feature_importance = pd.DataFrame({'feature': X.columns,
                                   'importance': rf.feature_importances_})

print(feature_importance.sort_values('importance', ascending=False))
