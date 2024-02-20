import pandas as pd
import numpy as np
import requests
import json
import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc, dash_table, callback
import dash_auth


from eviction_analysis_func import bar_by_cat, geo_by_cat_graph, bar_trace, \
    flat_fee_graph, mopen_graph, hr_worked_graph, amt_billed_graph, num_of_tks_graph, \
    time_taken_graph, cost_graph, profit_graph, hrs_graph

# load the row data from elite
df_elite_raw = pd.read_csv('evict_elite_info_raw.csv')
df_elite = pd.read_csv('evict_elite_info.csv')


def convert_to_float(x):
    if 'days' in x:
        # x.strip(' days')
        z = x.replace(' days', '')
        z = z.replace('days', '')
        z = z.replace(' ', '')
        return z
    elif 'day' in x:
        z = x.replace(' day', '')
        z = z.replace('day', '')
        z = z.replace(' ', '')
        return z


df_elite['time_taken'] = df_elite['time_taken'].apply(convert_to_float)
df_elite['time_taken'] = df_elite['time_taken'].astype(float)

# convert the date columns to datetime format
df_elite_raw['tworkdt'] = pd.to_datetime(df_elite_raw['tworkdt'],
                                         format='%Y-%m-%d')

# rename the tstatus for df_elite to more understandable names
df_elite_raw['tstatus'] = df_elite_raw.tstatus.replace({'B': 'Billed', 'AD': 'Adjusted',
                                                        'BNP': 'Write-off', 'BNC': 'Cancelled'})

# generate the year_month column for df_elite_raw
df_elite_raw['work_year_month'] = df_elite_raw['tworkdt'].dt.to_period(
    'M').astype(str)
df_elite_raw['work_year_month'] = pd.to_datetime(
    df_elite_raw['work_year_month'])

# seperate df_elite to client1_df and client2_df based on the first
# 5 digit of matter_id (tmatter column)
# *
client_dict = {}
for index, row in df_elite.drop_duplicates().iterrows():
    key = str(row['tmatter'])[:5]
    if key not in client_dict:
        client_dict[key] = row['clname1']

client_list = list(client_dict.values())
print(f'the client list is {client_list}')
client1_df = df_elite[df_elite['tmatter'].str[:5] == client_list[0]]
client2_df = df_elite[df_elite['tmatter'].str[:5] == client_list[1]]
print(f'the number of rows in client1_df is {len(client1_df)}',
      f'the number of rows in client2_df is {len(client2_df)}',
      f'and the number of rows in df_elite is {len(df_elite)}')


# add the fips code for each county
fips_code = {'Dallas': 48113, 'Mclennan': 48309, 'Taylor': 48441,
             'Tarrant': 48439, 'Denton': 48121, 'Travis': 48453,
             'Collin': 48085, 'Comal': 48091, 'Smith': 48423,
             'Williamson': 48491}

# assign the fips code to each county in the df, assign 00000 to nan values
df_elite['fips'] = df_elite['COUNTY'].map(fips_code).fillna('00000')


# Remove outlier rows:
df_elite = df_elite[df_elite['COUNTY'] != 'N/A - General legal advice']
df_elite = df_elite[df_elite['COUNTY'] != 'General legal advice']

# Rename the columns:
df_elite.rename(columns={'mmatter': 'matter_id', 'clname1': 'client_name',
                         'mdesc1': 'client_description', 'pdesc': 'practice_code',
                         'mopendt': 'matter_open_date', 'COUNTY': 'county',
                         'CATEGORY': 'dispute_category'}, inplace=True)

# Extract the year-month from each date
df_elite['matter_open_date'] = pd.to_datetime(df_elite['matter_open_date'])
df_elite['year_month'] = df_elite['matter_open_date'].dt.to_period(
    'M').astype(str)

# path to your USA county fips code json file
file_path = "USA-geojson-counties-fips.json"

with open(file_path, 'r') as f:
    counties = json.load(f)


# Filter for only Texas counties (fips codes beginning with '48').
filtered_counties = {"type": "FeatureCollection",
                     "features": [county for county in counties['features'] if county['id'].startswith('48')]}

# example DataFrame
dfs = pd.DataFrame({
    "fips": df_elite['fips'].tolist(),
    "county": df_elite['county'].tolist()
})

# filter the DataFrame for only Texan counties
dfs = dfs[dfs['county'].notna()]
dfs = dfs[dfs['fips'] != '00000']

# Compute number of instances for each county
county_counts = df_elite['fips'].value_counts().reset_index()
county_counts.columns = ['fips', 'counts']

# Merge to get county names for each FIPS code
county_counts = county_counts.merge(df_elite[['fips', 'county']].drop_duplicates(),
                                    on='fips', how='left')

# define the color scale for the map
client1 = client_list[0]
client2 = client_list[1]
client_color_discrete_map = {client1: '#FFD700', client2: '#87CEFA'}

# Compute the number of matters for each county
# and for each client
num_of_matters = df_elite['tmatter'].nunique()
client1_num_of_matters = client1_df['tmatter'].nunique()
client2_num_of_matters = client2_df['tmatter'].nunique()

# read in the cost data
df_cost = pd.read_csv('evict_elite_cost_info_grouped.csv')
df_cost_raw = pd.read_csv('evict_elite_cost_info_raw.csv')
hrs_df = pd.read_csv('work_by_hours.csv')

# join the cost data to df_elite to get df_profit
df_profit = df_elite.merge(df_cost, left_on='tmatter',
                           right_on='matter_id', how='left')

# use an online css style
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                url_base_pathname='/dash_apps/evict_dashboard/')

# define the "Go to top element"
gototop_html_div = html.Div(children=[html.A('Go to Top', href='#page-top')],
                            style={'display': 'flex', 'justifyContent': 'space-around'})

# run with gunicorn -w 1 --bind 0.0.0.0:8082 --daemon eviction_analysis:server
server = app.server

# set up authentication
VALID_USERNAME_PASSWORD_PAIRS = {
    'phelpsadmin': 'evictiondashboard!'
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS)


app.layout = html.Div([
    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
             children=[
        html.Img(
            src='https://www.phelps.com/cached/40026/images/logo-blue.svg',
            style={'height': '50px', 'width': 'auto', 'marginRight': 'auto'}
        )]),
    html.H1('Phelps Eviction Analysis', style={'marginLeft': 'auto', 'marginRight': 'auto',
                                               'alignSelf': 'center', 'text-align': 'center'}),
    html.Div(id='page-top', style={'display': 'flex', 'justifyContent': 'space-around'}, children=[
        html.Div(style={'width': '40%'}, children=[
            html.H3('Client:'),
            dcc.Dropdown(
                id='client-dropdown',
                options=[{'label': value, 'value': key}
                         for key, value in client_dict.items()],
                value=None)
        ]),

        html.Div(style={'width': '40%'}, children=[
            html.H3('Category:'),
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label': i, 'value': i}
                         for i in df_elite['dispute_category'].unique()],
                multi=True
            ),
        ]),

    ]),

    dcc.Tabs(
        id="tabs-for-graphs", value='mopendt_graph',
        children=[
            dcc.Tab(label='Timely Data', value='mopendt_graph'),
            dcc.Tab(label='Hours Worked', value='hr_worked_graph'),
            dcc.Tab(label='Amount Billed', value='amt_billed_graph'),
            dcc.Tab(label='Number of Tks', value='num_of_tks_graph'),
            dcc.Tab(label='Time Taken', value='time_taken_graph'),
            dcc.Tab(label='Cost', value='cost_graph'),
            dcc.Tab(label='Profit', value='profit_graph'),
            dcc.Tab(label='Flat Fee', value='flat_fee_graph', children=[
                    html.I(
                        'Please setup the expected profit margin(in decimals, for example 20% => 0.2) to determine the flat fee.'),
                    html.I('The default value is 20%.'),
                    html.Br(),
                    dcc.Input(id='expected-profit-margin', type='number',
                              placeholder='Input the expected profit margin'),
                    html.Div(id='data-table')]),
            dcc.Tab(label='Hrs by different level', value='hrs_worked_billed_graph', children=[
                html.H3('department:'),
                dcc.Dropdown(
                    id='department-dropdown',
                    options=[{'label': i, 'value': i}
                             for i in hrs_df['department'].unique()],
                    multi=True),
                dcc.Dropdown(
                    id='location-dropdown',
                    options=[{'label': i, 'value': i}
                             for i in hrs_df['location'].unique()],
                    multi=True),
            ])],
    ),
    html.Div(id="num-of-matters-info",
             style={'marginLeft': 'auto', 'marginRight': 'auto', 'alignSelf': 'center', 'text-align': 'center'}),
    html.Div(id="tabs-content-graphs"),

    html.A("Go to Top", id="go-to-top-button", href="#page-top", style={
        'position': 'fixed',
        'bottom': '15%',  # 10% from the bottom of the screen
        'right': '2%',   # 2% from the right side of the screen
        'zIndex': 1000,  # ensure it's above other items
        'padding': '8px 15px',
        'background-color': '#333',
        'color': 'white',
        'border-radius': '5px',
        'text-decoration': 'none',
        'font-weight': 'bold', })


], style={'backgroundColor': '#f5f5f5', 'padding': '10px'})


@app.callback(
    [Output("num-of-matters-info", "children"),
     Output("tabs-content-graphs", "children"),
     Output('data-table', 'children')],
    [Input("tabs-for-graphs", "value"),
     Input("client-dropdown", "value"),
     Input("category-dropdown", "value"),
     Input('expected-profit-margin', 'value'),
     Input('department-dropdown', 'value'),
     Input('location-dropdown', 'value')])
def render_content(tab, selected_client, selected_category, expected_profit_margin, selected_department, selected_location):
    df_profit = df_elite.merge(
        df_cost, left_on='tmatter', right_on='matter_id', how='left')
    df_hours_by_level = pd.read_csv('evict_elite_hours_by_level.csv')
    if selected_client and selected_category:
        df_profit = df_profit.loc[(df_profit['tmatter'].str[:5] == selected_client) &
                                  (df_profit['dispute_category'].isin(selected_category)), :]
        df_hours_by_level = df_hours_by_level.loc[(df_hours_by_level['matter_id'].str[:5] == selected_client) &
                                                  (df_hours_by_level['category'].isin(selected_category)), :]
    elif selected_client and not selected_category:
        df_profit = df_profit.loc[df_profit['tmatter'].str[:5]
                                  == selected_client, :]
        df_hours_by_level = df_hours_by_level.loc[df_hours_by_level['matter_id'].str[:5]
                                                  == selected_client, :]
    elif not selected_client and selected_category:
        df_profit = df_profit.loc[df_profit['dispute_category'].isin(
            selected_category), :]
        df_hours_by_level = df_hours_by_level.loc[df_hours_by_level['category'].isin(
            selected_category), :]
    else:
        df_profit = df_profit.copy()
        df_hours_by_level = df_hours_by_level.copy()

    grouped_df = df_profit.groupby(
        ['year_month', 'dispute_category']).size().reset_index(name='counts')
    grouped_df['year_month'] = pd.to_datetime(grouped_df['year_month'])

############################################### Flat Fee###############################################
    if tab == 'flat_fee_graph':
        return flat_fee_graph(df_profit, expected_profit_margin)

    ############################################### Timely Data###############################################
    elif tab == 'mopendt_graph':
        return mopen_graph(grouped_df, selected_client, df_elite_raw, df_cost_raw)

    ############################################### Total Hours Worked###############################################
    elif tab == 'hr_worked_graph':
        return hr_worked_graph(selected_client, df_profit, df_hours_by_level, filtered_counties)

############################################### Amount Billed##########################################################################
    elif tab == 'amt_billed_graph':
        return amt_billed_graph(selected_client, df_elite, df_profit, filtered_counties, client_color_discrete_map, num_of_matters)

################################################# Num of Tks#########################################################
    elif tab == 'num_of_tks_graph':
        return num_of_tks_graph(selected_client, df_profit, df_elite, filtered_counties, client_color_discrete_map)

##################################################### Time Taken#########################################################
    elif tab == 'time_taken_graph':
        return time_taken_graph(selected_client, df_profit, df_elite, filtered_counties, client_color_discrete_map)

######################################################### Cost Graph##############################################################
    elif tab == 'cost_graph':
        return cost_graph(df_profit, filtered_counties)

#################################################### Profit Graph##############################################################
    elif tab == 'profit_graph':
        return profit_graph(df_profit, filtered_counties)

    elif tab == 'hrs_worked_billed_graph':
        return hrs_graph(selected_department, selected_location)


if __name__ == '__main__':
    app.run_server(debug=True)
