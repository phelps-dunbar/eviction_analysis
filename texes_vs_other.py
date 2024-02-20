# this script is for testing if the the eviction analysis
# done in Texas area is different from other areas

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import dash
import json
from eviction_analysis_func import *

# read in the data
df = pd.read_csv('eviction_data_full.csv')

# combine the client address from 6 columns into 1
df['client_address_full'] = np.nan
df['client_address_full'] = df['client_address1'].fillna('') + ' ' + \
    df['client_address2'].fillna('') + ' ' + \
    df['client_address3'].fillna('') + ' ' + \
    df['client_address4'].fillna('') + ' ' + \
    df['client_address5'].fillna('') + ' ' + \
    df['client_address6'].fillna('')

# get the state of the data
# by using the client address and ask gpt 3.5
# to get the state of the client address
df['state'] = "NA"
df['state'] = df['state'].astype(str)

''' this part is done now
for i in range(len(df)):
    df.loc[i, 'state'] = get_state_from_address(
        df.loc[i, 'client_address_full'])
    print(f'row number {i} is done')

# save the result to csv
df.to_csv('test.csv', index=False)
'''

# read in the data
df_state = pd.read_csv('test.csv')
df_grouped = pd.read_csv('eviction_data_grouped.csv')

# attach the state info from df_state to df_grouped
# primary key being the matter_id
df = pd.merge(df_grouped, df_state[['matter_id', 'state']],
              how='left', on='matter_id')
df = df.drop_duplicates(subset=['matter_id'], keep='first')

# write the data to csv
df.to_csv('eviction_data_grouped_2.csv', index=False)

# get the data for Texas and other states
df_tx = df[df['state'] == 'Texas']
df_other = df[df['state'] != 'Texas']

# the null statement for the hypothesis shall be
# the mean of billed hours for Texas is the same as
# the mean of billed hours for other states
# the alternative statement for the hypothesis shall be
# the mean of billed hours for Texas is different from
# the mean of billed hours for other states

# first we need to test the normality of the data
# by using shapiro test
tx_billed_hours = df_tx['billed_hours']
non_tx_billed_hours = df_other['billed_hours']
check_normality(tx_billed_hours)
check_normality(non_tx_billed_hours)

# looks like both value are not normally distributed
# let's draw some boxplots to see if there are any outliers

# boxplot for Texas
plt.boxplot(tx_billed_hours)
plt.title('Texas billed hours')
plt.show()

# boxplot for other states
plt.boxplot(non_tx_billed_hours)
plt.title('Other states billed hours')
plt.show()

# looks like there are some outliers in both data
# look into the outliers in Texas
# print(df_tx.billed_hours.sort_values(ascending=False).head(10))


# generate a simply dash app to show the histogram
# of billed hours for each state

# create the app
app = dash.Dash()

# create the layout and add a list to select in dash for each state
# in the df data frame
# Filter out null values from the 'state' column in the DataFrame
df_states = df['state'].dropna().unique()

options = [{'label': i, 'value': i} for i in df_states]
options = json.loads(json.dumps(options))

app.layout = html.Div([
    html.H1('Eviction Analysis'),
    html.Div([
        dcc.Dropdown(
            id='state',
            options=options,
            value='Texas'
        )
    ]),
    dcc.Graph(id='eviction-graph')
])


@callback(
    Output('eviction-graph', 'figure'),
    [Input('state', 'value')]
)
def update_figure(selected_state):
    filtered_df = df[df.state == selected_state]
    # generate the histogram
    hist_graph = px.histogram(filtered_df, x='billed_hours',
                              nbins=20, title='Billed Hours')
    return hist_graph


# run the app
if __name__ == '__main__':
    app.run_server(debug=True)
