import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from insight_func import get_insights

# read in the data
df = pd.read_csv('evict_elite_info.csv')

# rename the columns
df = df.rename(columns={'tmatter': 'matter_id', 'clname1': 'client_name',
                        'mdesc1': 'matter_description', 'opendate': 'open_date',
                        'pdesc': 'practice_code', 'mopendt': 'matter_open_date',
                        'COUNTY': 'county', 'CATEGORY': 'category', })

# print the columns of the dataframe
print(df.columns)

# read in the timecard data
path = '../Bill_meeting_20240221/eviction_matter_tk_data.csv'
df_tc = pd.read_csv(path)

# read in the real county data
county_df_path = '../Bill_meeting_20240221/zip_test.xlsx'
df_zip = pd.read_excel(county_df_path, sheet_name='zip_test')

# merge the data
df_zip = df_zip.merge(df[['matter_id', 'client_name', 'category',
                          'total_hours_worked', 'total_amount_billed']], how="left",
                      left_on="matter_id", right_on="matter_id")

# drop the na values
df_zip = df_zip.dropna()
df_zip.to_csv("zip_test.csv", index=False)

# create the dash app
app = dash.Dash(__name__)

# create the app layout
header = html.Div(
    [
        html.H1("Flat Fee Calculator for Texas Eviction Cases",
                className="header-title"),
    ],
    className="header",
)

controls = html.Div(
    [
        html.Div(
            [
                html.H2("Filter the Data", className="control_label"),
                dcc.RadioItems(
                    id='radio-buttons',
                    options=[
                        {'label': 'County', 'value': 'county'},
                        {'label': 'Client', 'value': 'client'},
                        {'label': 'Category', 'value': 'category'}
                    ], value='county'),
                dcc.Graph(id="overall-graph"),
            ],
            className="control_graph",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Select a county", className="control_label"),
                        dcc.Dropdown(
                            id="county-dropdown",
                            options=[{"label": county, "value": county}
                                     for county in df["county"].dropna().unique()],
                            value=None,
                            multi=True,
                        ),
                    ],
                    className="control_item",
                ),
                html.Div(
                    [
                        html.Div("Select a client", className="control_label"),
                        dcc.Dropdown(
                            id="client-dropdown",
                            options=[{"label": client, "value": client}
                                     for client in df["client_name"].dropna().unique()],
                            value=None,
                            multi=True,
                        ),
                    ],
                    className="control_item",
                ),
                html.Div(
                    [
                        html.Div("Select a category",
                                 className="control_label"),
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=[{"label": category, "value": category}
                                     for category in df["category"].dropna().unique()],
                            value=None,
                            multi=True,
                        ),
                    ],
                    className="control_item",
                )
            ],
            className="selector_container",
        ),
    ],
    className="controls_container",
)

controls_zip = html.Div(
    [
        html.Div(
            [
                html.H2("Filter the Data", className="control_label"),
                dcc.RadioItems(
                    id='radio-buttons-zip',
                    options=[
                        {'label': 'Property County', 'value': 'real_county'},
                        {'label': 'Property City', 'value': 'property_city'},
                        {'label': 'Category', 'value': 'category'},
                        {'label': 'Client', 'value': 'client'},
                    ], value='real_county'),
                dcc.Graph(id="overall-graph-zip"),
            ],
            className="control_graph",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Select a client",
                                 className="control_label"),
                        dcc.Dropdown(
                            id="client-dropdown-zip",
                            options=[{"label": client, "value": client}
                                     for client in df_zip["client_name"].dropna().unique()],
                            value=None
                        ),
                    ],
                    className="control_item",
                ),
                html.Div(
                    [
                        html.Div("Select a real county",
                                 className="control_label"),
                        dcc.Dropdown(
                            id="real-county-dropdown-zip",
                            options=[{"label": real_county, "value": real_county}
                                     for real_county in df_zip["real_county"].dropna().unique()],
                            value=None,
                            multi=True,
                        ),
                    ],
                    className="control_item",
                ),
                html.Div(
                    [
                        html.Div("Select a property city",
                                 className="control_label"),
                        dcc.Dropdown(
                            id="property-city-dropdown-zip",
                            options=[{"label": property_city, "value": property_city}
                                     for property_city in df_zip["property_city"].dropna().unique()],
                            value=None,
                            multi=True,
                        ),
                    ],
                    className="control_item",
                ),
                html.Div(
                    [
                        html.Div("Select a category",
                                 className="control_label"),
                        dcc.Dropdown(
                            id="category-dropdown-zip",
                            options=[{"label": category, "value": category}
                                     for category in df_zip["category"].dropna().unique()],
                            value=None,
                            multi=True,
                        )
                    ],
                    className="control_item",
                ),

            ],
            className="selector_container",
        ),
    ],
    className="controls_container   ",
)

insights_and_graphs = html.Div(
    [
        html.Div(
            [
                html.H2("Matter Distribution", className="graph_title"),
                dcc.Graph(id="results-graph"),
            ],
            className="graph_container",
        ),
        html.Div(
            [
                html.H2("Insights", className="graph_title"),
                html.Div(id="insights"),
                html.Div(id="stats-box"),
                html.H2("Trim the Data", className="graph_title"),
                dcc.Checklist(
                    id="remove-data-checklist",
                    options=[
                        {"label": "Remove Top 5%", "value": "TOP_5"},
                        {"label": "Remove Top 10%", "value": "TOP_10"},
                    ],
                    value=[],
                ),
            ],
            className="insights_container",
        ),
    ],
    className="results_container",
)

datatable_container = html.Div(
    [
        html.H2("Data Table", className="graph_title"),
        dash_table.DataTable(id='data_table',),
    ],
    className="data_table_container",
)

# add the hour by timekeeper level graph
tk_hour_graph = html.Div(
    [
        html.H2("Total Hours Worked by Timekeeper", className="graph_title"),
        dcc.Graph(id="tk-hour-graph"),
    ],
    className="tk_hour_container",
)

# add the timeline of the matters
timeline = html.Div(
    [
        html.H2("Timeline of the Matters", className="graph_title"),
        dcc.Graph(id="timeline-graph"),
    ],
    className="timeline_container",
)

# add the time taken to complete a matter
time_taken = html.Div(
    [
        html.H2("Time Taken to Complete a Matter", className="graph_title"),
        dcc.Graph(id="time-taken-graph"),
    ],
    className="time_taken_container",
)

# add the billed amount graph
billed_graph = html.Div(
    [
        html.H2("Matter Distribution", className="graph_title"),
        dcc.Graph(id="billed-graph"),
    ]
)

dashtable_container_2 = html.Div(
    [
        html.H2("Data Table", className="graph_title"),
        dash_table.DataTable(id='data_table_2',
                             columns=[{"name": i, "id": i}
                                      for i in df_zip.iloc[0:20].columns],
                             data=df_zip.iloc[0:20].to_dict('records'),
                             filter_action="native",
                             sort_action="native",
                             )
    ],
    className="data_table_container",
)

# add the population graph
population_graph = html.Div(
    [
        html.H2("Population Distribution", className="graph_title"),
        dcc.Graph(id="population-graph"),
    ]
)

tab1_content = html.Div([
    header,
    controls,
    insights_and_graphs,
    datatable_container,
    tk_hour_graph,
    timeline,
    time_taken,
])

tab1 = dcc.Tab(label='original data', children=[tab1_content])

tab2 = dcc.Tab(
    label='WIP',
    children=[
        html.Div(
            [
                controls_zip,
                billed_graph,
                dashtable_container_2,
                population_graph,
            ]
        )
    ]
)

tabs = dcc.Tabs(children=[tab1, tab2])

app.layout = html.Div([
    tabs
])


@app.callback(
    [Output('stats-box', 'children'),
     Output('overall-graph', 'figure'),
     Output('results-graph', 'figure'),
     Output('insights', 'children'),
     Output('data_table', 'data'),
     Output('data_table', 'columns'),
     Output('tk-hour-graph', 'figure'),
     Output('timeline-graph', 'figure'),
     Output('time-taken-graph', 'figure'),
     Output('overall-graph-zip', 'figure'),
     Output('billed-graph', 'figure'),
     Output('population-graph', 'figure'),
     Output('data_table_2', 'data'),],
    [Input('county-dropdown', 'value'),
     Input('category-dropdown', 'value'),
     Input('client-dropdown', 'value'),
     Input('radio-buttons', 'value'),
     Input('remove-data-checklist', 'value'),
     Input('results-graph', 'clickData'),
     Input('real-county-dropdown-zip', 'value'),
     Input('property-city-dropdown-zip', 'value'),
     Input('category-dropdown-zip', 'value'),
     Input('client-dropdown-zip', 'value'),
     Input('radio-buttons-zip', 'value'),]
)
def update_output(selected_county, selected_category, selected_client,
                  radio_buttons, remove_data, clickData, selected_real_county,
                  selected_property_city, selected_category_zip, selected_client_zip,
                  radio_buttons_zip):
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

    filtered_df_tc = df_tc[df_tc['matter_id'].isin(
        filtered_df['matter_id'])]

    # filter the df_zip
    filtered_df_zip = df_zip
    if selected_real_county:
        filtered_df_zip = filtered_df_zip[filtered_df_zip['real_county'].isin(
            selected_real_county)]
    if selected_property_city:
        filtered_df_zip = filtered_df_zip[filtered_df_zip['property_city'].isin(
            selected_property_city)]
    if selected_category_zip:
        filtered_df_zip = filtered_df_zip[filtered_df_zip['category'].isin(
            selected_category_zip)]
    if selected_client_zip:
        filtered_df_zip = filtered_df_zip[filtered_df_zip['client_name'] ==
                                          str(selected_client_zip)]

    # generate the overall histogram for each category, ordering by the number of cases descending
    if radio_buttons == 'category':
        # generate the overall histogram for each category, ordering by the number of cases descending
        overall_hist = filtered_df.groupby('category').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='category', x='counts', orientation='h',
                                  title='Number of Cases by Category',
                                  labels={'category': 'Category',
                                          'matter_id': 'Number of Cases'},
                                  text='counts',
                                  hover_data={'category': False, 'counts': True})
    elif radio_buttons == 'county':
        overall_hist = filtered_df.groupby('county').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='county', x='counts', orientation='h',
                                  title='Number of Cases by County',
                                  labels={'county': 'County',
                                          'matter_id': 'Number of Cases'},
                                  text='counts',
                                  hover_data={'county': False, 'counts': True})
    elif radio_buttons == 'client':
        overall_hist = filtered_df.groupby('client_name').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='client_name', x='counts', orientation='h',
                                  title='Number of Cases by Client',
                                  labels={'client_name': 'Client',
                                          'matter_id': 'Number of Cases'},
                                  text='counts',
                                  hover_data={'client_name': False, 'counts': True})

    # generate and return the stats and figure
    number_of_cases = filtered_df['matter_id'].nunique()
    mean_fee = round(filtered_df['total_amount_billed'].mean(), 2)
    median_fee = filtered_df['total_amount_billed'].median()
    std_fee = round(filtered_df['total_amount_billed'].std(), 2)
    # if (selected_county is not None) and (selected_county is not None) and (selected_client is not None):
    #    client_list = ["Monticello Asset Management, Inc.",
    #                   "Accolade Property Management, Inc."]
    #    print(f"'{selected_client}'", [
    #          f"'{client}'" for client in client_list], selected_client in client_list, 'true or not')
    #    insight = get_insights(str(selected_county), str(
    #        selected_category), str(selected_client))
    #    print(insight)
    # else:
    insight = "we only have insights when all three criteria are chosen for now"
    insight_box = html.Div([html.H3(insight)])
    stats_box = html.Div([
        html.H2('Statistics'),
        dcc.Markdown(f'Number of Cases: **{number_of_cases}**'),
        dcc.Markdown(f'Mean Total Amount Billed: **{mean_fee:.2f}**'),
        dcc.Markdown(f'Median Total Amount Billed: **{median_fee:.2f}**'),
        dcc.Markdown(
            f'Standard Deviation of Total Amount Billed: **{std_fee:.2f}**')
    ])

    fig = px.histogram(filtered_df, nbins=50, x='total_amount_billed',
                       title='Distribution of Total Amount Billed',)
    fig.update_xaxes(title_text='Total Amount Billed')
    fig.update_yaxes(title_text='Count')
    bin_width = (filtered_df['total_amount_billed'].max() -
                 filtered_df['total_amount_billed'].min()) / 50

    # generate the histogram for the timekeeper hours by tktitle, done
    tk_hour_hist = filtered_df_tc.groupby(by=['matter_id', 'timekeeper_title']).agg(
        {'total_work_hours': 'sum'}).reset_index()

    # sort the values by total_bill_hours
    tk_hour_hist = tk_hour_hist.sort_values(
        'total_work_hours', ascending=False)

    tk_hour_fig = px.bar(tk_hour_hist, x='matter_id', y='total_work_hours', color='timekeeper_title',
                         color_discrete_map={
                             'Associate': 'orange', 'Paralegal': 'yellow', 'Partner': 'red', "Clerk": 'blue'},
                         title='Total Worked Hours by Timekeeper',
                         labels={'timekeeper_title': 'Timekeeper',
                                 'total_work_hours': 'Total Worked Hours'},
                         hover_data={'timekeeper_title': False, 'total_work_hours': True, })

    timeline_fig = px.scatter(filtered_df, x='matter_open_date', y='total_amount_billed', color='client_name',
                              title='Timeline of the Matters',
                              labels={'matter_open_date': 'Matter Open Date',
                                      'total_amount_billed': 'Total Amount Billed'},
                              hover_data={
                                  'matter_open_date': True, 'total_amount_billed': True, 'category': True},
                              color_continuous_scale=px.colors.sequential.Plasma)
    timeline_fig.update_layout(template='plotly_dark')

    # adjust the time_taken's dataformat to be in integer
    filtered_df['time_taken'] = filtered_df['time_taken'].astype(
        str).str.replace(' days', '').astype(int)

    time_taken_fig = px.histogram(filtered_df, x='time_taken',
                                  title='Time Taken to Complete a Matter',
                                  labels={'time_taken': 'Time Taken',
                                          'matter_id': "Matter ID"},
                                  hover_data={'time_taken': True,
                                              "matter_id": True},
                                  color_discrete_sequence=px.colors.qualitative.Pastel)
    time_taken_fig.update_layout(template='plotly_white')

    if clickData:
        selected_amount = clickData['points'][0]['x']
        filtered_df_new = filtered_df[(filtered_df['total_amount_billed'] <= selected_amount * 1.05) &
                                      (filtered_df['total_amount_billed'] >= (selected_amount - bin_width))]
        filtered_df_new = filtered_df_new[['matter_id', 'client_name', 'matter_description',
                                           'county', 'category', 'total_hours_worked', 'total_amount_billed']]
        filtered_df_new = filtered_df_new.sort_values(
            'total_amount_billed', ascending=False)
        # from the filtered_df_tc, generate the total_not_billed_hours
        # and total_bill_hours by each matter_id
        filtered_df_tc_new = filtered_df_tc[filtered_df_tc['matter_id'].isin(
            filtered_df_new['matter_id'])]
        filtered_df_tc_new = filtered_df_tc_new.groupby('matter_id').agg(
            {'non_billed_hours': 'sum', 'total_bill_hours': 'sum'}).reset_index()
        filtered_df_new = filtered_df_new.merge(
            filtered_df_tc_new, on='matter_id', how='left')
        data = filtered_df_new.to_dict('records')
        columns = [{'name': i, 'id': i} for i in filtered_df_new.columns]

    else:
        filtered_df_2 = filtered_df[['matter_id', 'client_name', 'matter_description',
                                     'county', 'category', 'total_hours_worked', 'total_amount_billed']]
        filtered_df_2 = filtered_df_2.sort_values(
            'total_amount_billed', ascending=False)
        data = filtered_df_2.to_dict('records')
        columns = [{'name': i, 'id': i} for i in filtered_df_2.columns]

    # generate the bill graph, rent graph and population graph
    if radio_buttons_zip == 'real_county':
        # generate the bill graph for each real county, ordering by the number of cases descending
        overall_hist_zip = filtered_df_zip.groupby('real_county').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist_zip = overall_hist_zip.sort_values(
            'counts', ascending=True)
        overall_hist_fig_zip = px.bar(overall_hist_zip, y='real_county', x='counts', orientation='h',
                                      title='Number of Cases by Real County',
                                      labels={'real_county': 'Real County',
                                              'matter_id': 'Number of Cases'},
                                      text='counts',
                                      hover_data={'real_county': False, 'counts': True})
    elif radio_buttons_zip == 'property_city':
        overall_hist_zip = filtered_df_zip.groupby('property_city').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist_zip = overall_hist_zip.sort_values(
            'counts', ascending=True)
        overall_hist_fig_zip = px.bar(overall_hist_zip, y='property_city', x='counts', orientation='h',
                                      title='Number of Cases by Property City',
                                      labels={'property_city': 'Property City',
                                              'matter_id': 'Number of Cases'},
                                      text='counts',
                                      hover_data={'property_city': False, 'counts': True})
    elif radio_buttons_zip == 'category':
        overall_hist_zip = filtered_df_zip.groupby('category').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist_zip = overall_hist_zip.sort_values(
            'counts', ascending=True)
        overall_hist_fig_zip = px.bar(overall_hist_zip, y='category', x='counts', orientation='h',
                                      title='Number of Cases by Category',
                                      labels={'category': 'Category',
                                              'matter_id': 'Number of Cases'},
                                      text='counts',
                                      hover_data={'category': False, 'counts': True})

    elif radio_buttons_zip == 'client':
        overall_hist_zip = filtered_df_zip.groupby('client_name').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist_zip = overall_hist_zip.sort_values(
            'counts', ascending=True)
        overall_hist_fig_zip = px.bar(overall_hist_zip, y='client_name', x='counts', orientation='h',
                                      title='Number of Cases by Client',
                                      labels={'client_name': 'Client',
                                              'matter_id': 'Number of Cases'},
                                      text='counts',
                                      hover_data={'client_name': False, 'counts': True})

    # generate the billed graph histogram
    billed_hist = px.histogram(filtered_df_zip, x='total_amount_billed',
                               title='Distribution of Total Amount Billed',
                               nbins=50, text_auto=True)
    billed_hist.update_xaxes(title_text='Total Amount Billed')
    billed_hist.update_yaxes(title_text='Count')

    # generate the population graph
    population_hist = px.bar(filtered_df_zip[['irs_estimated_population', 'real_county']].drop_duplicates(),
                             x='irs_estimated_population', y='real_county',
                             title='Population Distribution',
                             labels={'irs_estimated_population': 'Population',
                                     'real_county': 'Real County'},
                             text='irs_estimated_population',
                             hover_data={'irs_estimated_population': True, 'real_county': False})

    # data table for the second tab
    filtered_df_zip_2 = filtered_df_zip.to_dict('records')

    return stats_box, overall_hist_fig, fig, insight_box, data, columns, tk_hour_fig, \
        timeline_fig, time_taken_fig, overall_hist_fig_zip, billed_hist, population_hist, \
        filtered_df_zip_2


if __name__ == '__main__':
    app.run_server(debug=True)
