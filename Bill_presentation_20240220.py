import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# read in the data
df = pd.read_csv('evict_elite_info.csv')

# rename the columns
df = df.rename(columns={'tmatter': 'matter_id', 'clname1': 'client_name',
                        'mdesc1': 'matter_description', 'opendate': 'open_date',
                        'pdesc': 'practice_code', 'mopendt': 'matter_open_date',
                        'COUNTY': 'county', 'CATEGORY': 'category', })

# print the columns of the dataframe
print(df.columns)

# define a function for the insights


def get_insights(df, county, category, client):
    if client == 'Monticello Asset Management, Inc.':
        pass
    elif client == 'Accolade Property Management, Inc.':
        client_sentence = "Most cases fall under the non-payment eviction appeal category."


# create the dash app
app = dash.Dash(__name__)

# create the app layout
app.layout = html.Div([
    html.H1("Flat Fee Calculator for Texes Eviction Cases",
            style={'textAlign': 'center'}),
    html.Div([
        dcc.Dropdown(
            id='county-dropdown',
            options=[{'label': county, 'value': county}
                     for county in df['county'].dropna().unique()],
            value=None,
            placeholder="Select a county",
            multi=True,
            style={'width': '33%'}
        ),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': category, 'value': category}
                     for category in df['category'].dropna().unique()],
            value=None,
            placeholder="Select a category",
            multi=True,
            style={'width': '33%'}
        ),
        dcc.Dropdown(
            id='client-dropdown',
            options=[{'label': client, 'value': client}
                     for client in df['client_name'].dropna().unique()],
            value=None,
            placeholder="Select a client",
            multi=True,
            style={'width': '33%'}
        )], style={'display': 'flex', 'justify-content': 'space-around'}),
    html.Div(id='info-block', children=[
        dcc.Graph(id='overall-graph'),
        html.Div(id='stats-box'),
        html.Div(children=dcc.Checklist(
            id='remove-data-checklist',
            options=[
                {'label': 'Remove Top 5%', 'value': 'TOP_5'},
                {'label': 'Remove Top 10%', 'value': 'TOP_10'}],
            value=[]))
    ], style={'width': '40%', 'display': 'inline-block', 'justify-content': 'flex-start', 'align-items':  'flex-start'}),
    html.Div(id='graph-block',
             children=[html.H2(id='insights', children='Insights', style={'textAlign': 'center'}),
                       dcc.Graph(id='results-graph')], style={'width': '60%', 'display': 'inline-block', 'justify-content': 'flex-start', 'align-items':  'flex-start'}),
])


@app.callback(
    [Output('stats-box', 'children'),
     Output('overall-graph', 'figure'),
     Output('insights', 'children'),
     Output('results-graph', 'figure'),],
    [Input('county-dropdown', 'value'),
     Input('category-dropdown', 'value'),
     Input('client-dropdown', 'value'),
     Input('remove-data-checklist', 'value')]
)
def update_output(selected_county, selected_category, selected_client, remove_data):
    # filter the dataframe based on the selected dropdown values
    filtered_df = df
    if selected_county:
        filtered_df = filtered_df[filtered_df['county'].isin(selected_county)]
    if selected_category:
        filtered_df = filtered_df[filtered_df['category'].isin(
            selected_category)]
    if selected_client:
        filtered_df = filtered_df[filtered_df['client_name'].isin(
            selected_client)]

    if 'TOP_5' in remove_data:
        filtered_df = filtered_df[filtered_df['total_amount_billed']
                                  < filtered_df['total_amount_billed'].quantile(0.95)]
    elif 'TOP_10' in remove_data:
        filtered_df = filtered_df[filtered_df['total_amount_billed']
                                  < filtered_df['total_amount_billed'].quantile(0.90)]

    # generate the overall histogram for each category, ordering by the number of cases descending
    overall_hist = filtered_df.groupby('category').agg(
        {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
    overall_hist = overall_hist.sort_values('counts', ascending=True)

    overall_hist_fig = px.bar(overall_hist, y='category', x='counts', orientation='h',
                              title='Number of Cases by Category',
                              labels={'category': 'Category', 'matter_id': 'Number of Cases'})

    # generate and return the stats and figure
    number_of_cases = filtered_df['matter_id'].nunique()
    mean_fee = round(filtered_df['total_amount_billed'].mean(), 2)
    median_fee = filtered_df['total_amount_billed'].median()
    std_fee = round(filtered_df['total_amount_billed'].std(), 2)
    stats_box = html.Div([
        html.H2('Statistics'),
        html.P(f'Number of Cases: {number_of_cases}'),
        html.P(f'Mean Total Amount Billed: {mean_fee:.2f}'),
        html.P(f'Median Total Amount Billed: {median_fee:.2f}'),
        html.P(f'Standard Deviation of Total Amount Billed: {std_fee:.2f}')
    ])

    hist_data = filtered_df['total_amount_billed']
    hist_data_counts, hist_data_bins = np.histogram(hist_data, bins=50)

    fig = go.Figure(data=[go.Bar(
        x=hist_data_bins, y=hist_data_counts, text=hist_data_counts, textposition='auto',
        hovertemplate='Total Amount Billed: %{x:.2f}<br>Count: %{y}<extra></extra>')])

    fig.update_layout(
        title='Distribution of Total Amount Billed',
        xaxis_title='Total Amount Billed',
        yaxis_title='Count'
    )

    return stats_box, overall_hist_fig, "Results", fig


if __name__ == '__main__':
    app.run_server(debug=True)
