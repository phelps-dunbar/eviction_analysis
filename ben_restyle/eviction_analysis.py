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

app.layout = html.Div(
    [
        header,
        controls,
        insights_and_graphs,
        datatable_container,
        tk_hour_graph
    ],
    className="container",
)


@app.callback(
    [Output('stats-box', 'children'),
     Output('overall-graph', 'figure'),
     Output('results-graph', 'figure'),
     Output('insights', 'children'),
     Output('data_table', 'data'),
     Output('data_table', 'columns'),
     Output('tk-hour-graph', 'figure'),],
    [Input('county-dropdown', 'value'),
     Input('category-dropdown', 'value'),
     Input('client-dropdown', 'value'),
     Input('radio-buttons', 'value'),
     Input('remove-data-checklist', 'value'),
     Input('results-graph', 'clickData')]
)
def update_output(selected_county, selected_category, selected_client, radio_buttons, remove_data, clickData):
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

    if radio_buttons == 'category':
        # generate the overall histogram for each category, ordering by the number of cases descending
        overall_hist = filtered_df.groupby('category').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='category', x='counts', orientation='h',
                                  title='Number of Cases by Category',
                                  labels={'category': 'Category',
                                          'matter_id': 'Number of Cases'},
                                  hover_data={'category': False, 'counts': True})
    elif radio_buttons == 'county':
        overall_hist = filtered_df.groupby('county').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='county', x='counts', orientation='h',
                                  title='Number of Cases by County',
                                  labels={'county': 'County',
                                          'matter_id': 'Number of Cases'},
                                  hover_data={'county': False, 'counts': True})
    elif radio_buttons == 'client':
        overall_hist = filtered_df.groupby('client_name').agg(
            {'matter_id': 'nunique'}).reset_index().rename(columns={'matter_id': 'counts'})
        overall_hist = overall_hist.sort_values('counts', ascending=True)
        overall_hist_fig = px.bar(overall_hist, y='client_name', x='counts', orientation='h',
                                  title='Number of Cases by Client',
                                  labels={'client_name': 'Client',
                                          'matter_id': 'Number of Cases'},
                                  hover_data={'client_name': False, 'counts': True})

    # generate and return the stats and figure
    number_of_cases = filtered_df['matter_id'].nunique()
    mean_fee = round(filtered_df['total_amount_billed'].mean(), 2)
    median_fee = filtered_df['total_amount_billed'].median()
    std_fee = round(filtered_df['total_amount_billed'].std(), 2)
    if (selected_county is not None) and (selected_county is not None) and (selected_client is not None):
        client_list = ["Monticello Asset Management, Inc.", "Accolade Property Management, Inc."]
        print(f"'{selected_client}'", [f"'{client}'" for client in client_list], selected_client in client_list, 'true or not')
        insight = get_insights(str(selected_county), str(selected_category), str(selected_client))
        print(insight)
    else:
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
                       title='Distribution of Total Amount Billed')
    fig.update_xaxes(title_text='Total Amount Billed')
    fig.update_yaxes(title_text='Count')

    # generate the histogram for the timekeeper hours by tktitle
    tk_hour_hist = filtered_df_tc.groupby(by=['matter_id', 'timekeeper_title']).agg(
        {'total_work_hours': 'sum'}).reset_index()

    # sort the values by total_bill_hours
    tk_hour_hist = tk_hour_hist.sort_values(
        'total_work_hours', ascending=False)

    tk_hour_fig = px.bar(tk_hour_hist, x='matter_id', y='total_work_hours', color='timekeeper_title',
                         title='Total Worked Hours by Timekeeper',
                         labels={'timekeeper_title': 'Timekeeper',
                                 'total_work_hours': 'Total Worked Hours'},
                         hover_data={'timekeeper_title': False, 'total_work_hours': True, })

    if clickData:
        selected_amount = clickData['points'][0]['x']
        filtered_df_new = filtered_df[filtered_df['total_amount_billed']
                                      <= selected_amount]
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
        return stats_box, overall_hist_fig, fig, insight_box, data, columns, tk_hour_fig
    else:
        return stats_box, overall_hist_fig, fig, insight_box, [], [], tk_hour_fig


if __name__ == '__main__':
    app.run_server(debug=True)
