# this script is for the seasonality analysis

import pandas as pd

# read in the data
df = pd.read_csv('eviction_data_grouped.csv')
print(df.head())

# generate the year and month columns from the matter_open_date
df['matter_open_date'] = pd.to_datetime(df['matter_open_date'])
df['year'] = df['matter_open_date'].dt.year
df['month'] = df['matter_open_date'].dt.month

# count the number of matters opened in each month
df_count = df.groupby(['year', 'month']).count().reset_index()
df_count = df_count[['year', 'month', 'matter_id']]
df_count.columns = ['year', 'month', 'matter_count']

# generate a graph for the number of matters opened in each month
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('darkgrid')
sns.set_context('talk')
sns.set_palette('husl', 6)

plt.figure(figsize=(12, 8))
sns.lineplot(x='month', y='matter_count', hue='year', data=df_count)
plt.title('Number of Matters Opened in Each Month')
plt.xlabel('Month')
plt.ylabel('Number of Matters')
plt.legend(loc='upper right')
plt.savefig('matter_count.png')
plt.show()

# now do the dollor amount by month
df_dollor = df.groupby(['year', 'month']).sum().reset_index()
df_dollor = df_dollor[['year', 'month', 'worked_dollars', 'billed_dollars']]
df_dollor.columns = ['year', 'month', 'worked_dollars', 'billed_dollars']

# generate a graph for the number of matters opened in each month
plt.figure(figsize=(12, 8))
sns.lineplot(x='month', y='worked_dollars', hue='year', data=df_dollor)
plt.title('Total Worked Dollars in Each Month')
plt.xlabel('Month')
plt.ylabel('Total Worked Dollars')
plt.legend(loc='upper right')
plt.savefig('worked_dollars.png')
plt.show()