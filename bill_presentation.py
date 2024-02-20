import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, callback, Output, Input
import plotly.graph_objects as go

# Read data from CSV file
df = pd.read_csv('WIP_data_2.csv', header=0, index_col=0)
df = df.drop_duplicates()
df = df.drop(['unbilled_hours_x', 'unbilled_hours_y'], axis=1)
df = df.dropna()
print(f'the number of rows is {len(df)}')

# drop the rows with worked_dollars < 0
df = df[df['worked_dollars'] > 0]

# Create Dash app layout
app = dash.Dash(__name__, external_stylesheets=['style.css'])
app.layout = html.Div([

    html.Div([
        # add the state filter
        html.Label('State:'),
        dcc.Dropdown(id='state-picker',
                     options=[{'label': i, 'value': i} for i in df.state.unique()]),
    ], style={'display': 'inline-block', 'width': '25%'}),
    html.Div([
        # add the matter open year filter
        html.Label('Matter Open Year:'),
        dcc.Dropdown(id='matter_open_year-picker',
                     options=[{'label': i, 'value': i} for i in df.matter_open_year.unique()]),
    ], style={'display': 'inline-block', 'width': '25%'}),
    html.Div([
        # add the location filter
        html.Label('Location:'),
        dcc.Dropdown(id='location-picker',
                     options=[{'label': i, 'value': i} for i in df.location.unique()]),
    ], style={'display': 'inline-block', 'width': '25%'}),
    html.Div([
        # add the department filter
        html.Label('Department:'),
        dcc.Dropdown(id='department-picker',
                     options=[{'label': i, 'value': i} for i in df.department.unique()]),
    ], style={'display': 'inline-block', 'width': '25%'}),

    # add the tabs
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label="Historical Information", value='tab-1'),
        dcc.Tab(label="Predictive Information", value='tab-2'),
    ]),
    html.Div(id='tabs-content'),
    # add the worked dollars filter
    html.Div([
        html.Label('Min Worked Dollars:'),
        dcc.Input(id='min-worked-dollars', type='number',
                  value=df['worked_dollars'].min()),
        html.Label('Max Worked Dollars:'),
        dcc.Input(id='max-worked-dollars', type='number',
                  value=df['worked_dollars'].max()),
    ], style={'display': 'block', 'margin-bottom': '20px'}),
    # add the worked hours filter
    html.Div([
        html.Label('Min Worked Hours:'),
        # Default to min value in dataset
        dcc.Input(id='min-worked-hours', type='number',
                  value=df['worked_hours'].min(), step=0.01),
        html.Label('Max Worked Hours:'),
        # Default to max value in dataset
        dcc.Input(id='max-worked-hours', type='number',
                  value=df['worked_hours'].max(), step=0.01),
    ], style={'display': 'block', 'margin-bottom': '20px'}),
    # add a text box for inputted desired number of bins
    html.Div([
        html.Label('Number of Bins:'),
        dcc.Input(id='num-bins', type='number', value=20),
    ], style={'display': 'block', 'margin-bottom': '20px'}),
    # add an input box for the expected flat fee
    html.Div([
        html.Label('Flat Fee:'),
        dcc.Input(id='flat-fee', type='number', value=1000),
    ], style={'display': 'block', 'margin-bottom': '20px'}),
    # add a slider for the expected profit margin
    html.Div([
        html.Label('Profit Margin:'),
        dcc.Slider(id='profit-margin-slider', min=0, max=100, step=1, value=0),
    ], style={'display': 'block', 'margin-bottom': '20px'}),
    html.Div(id='output'),
])

# Define callback function to update histogram graph


@callback(
    Output(component_id='output', component_property='children'),
    [
        Input(component_id='state-picker', component_property='value'),
        Input(component_id='matter_open_year-picker',
              component_property='value'),
        Input(component_id='location-picker', component_property='value'),
        Input(component_id='department-picker', component_property='value'),
        Input(component_id='min-worked-dollars', component_property='value'),
        Input(component_id='max-worked-dollars', component_property='value'),
        Input(component_id='min-worked-hours', component_property='value'),
        Input(component_id='max-worked-hours', component_property='value'),
        Input(component_id='num-bins', component_property='value'),
        Input(component_id='flat-fee', component_property='value'),
        Input(component_id='profit-margin-slider', component_property='value'),
        Input(component_id='tabs', component_property='value'),
    ]
)
def update_histogram(state, matter_open_year, location, department,
                     min_dollars, max_dollars, min_hours, max_hours,
                     num_bins, flat_fee, profit_margin, tab_value):
    if state is None and matter_open_year is None and location is None and department is None:
        df_filtered = df
    elif state is None and matter_open_year is None and location is None:
        df_filtered = df[df.department == department]
    elif state is None and matter_open_year is None and department is None:
        df_filtered = df[df.location == location]
    elif state is None and location is None and department is None:
        df_filtered = df[df.matter_open_year == matter_open_year]
    elif matter_open_year is None and location is None and department is None:
        df_filtered = df[df.state == state]
    elif state is None and matter_open_year is None:
        df_filtered = df[(df.location == location) &
                         (df.department == department)]
    elif state is None and location is None:
        df_filtered = df[(df.matter_open_year == matter_open_year)
                         & (df.department == department)]
    elif state is None and department is None:
        df_filtered = df[(df.matter_open_year == matter_open_year)
                         & (df.location == location)]
    elif matter_open_year is None and location is None:
        df_filtered = df[(df.state == state) & (df.department == department)]
    elif matter_open_year is None and department is None:
        df_filtered = df[(df.state == state) & (df.location == location)]
    elif location is None and department is None:
        df_filtered = df[(df.state == state) &
                         (df.matter_open_year == matter_open_year)]
    elif state is None:
        df_filtered = df[(df.matter_open_year == matter_open_year) &
                         (df.location == location) & (df.department == department)]
    elif matter_open_year is None:
        df_filtered = df[(df.state == state) &
                         (df.location == location) & (df.department == department)]
    elif location is None:
        df_filtered = df[(df.state == state) &
                         (df.matter_open_year == matter_open_year) & (df.department == department)]
    elif department is None:
        df_filtered = df[(df.state == state) &
                         (df.matter_open_year == matter_open_year) & (df.location == location)]

    if tab_value == 'tab-1':
        # filter by the min and max worked dollars
        df_filtered = df_filtered[(df_filtered['worked_dollars'] >= min_dollars) & (
            df_filtered['worked_dollars'] <= max_dollars)]

        # filter by the min and max worked hours
        df_filtered = df_filtered[(df_filtered['worked_hours'] >= min_hours) & (
            df_filtered['worked_hours'] <= max_hours)]

        # calculate the mean and std of worked dollars
        mean_dollars = df_filtered['worked_dollars'].mean()
        std_dollars = df_filtered['worked_dollars'].std()

        # calculate the mean and std of worked hours
        mean_hours = df_filtered['worked_hours'].mean()
        std_hours = df_filtered['worked_hours'].std()

        # create html elements to display the mean and std of worked dollars and worked hours
        dollars_div = html.Div([
            html.H3('Mean Worked Dollars: {:.2f}'.format(mean_dollars)),
            html.H3('Std Worked Dollars: {:.2f}'.format(std_dollars)),
        ], style={'text-align': 'center'})
        hours_div = html.Div([
            html.H3('Mean Worked Hours: {:.2f}'.format(mean_hours)),
            html.H3('Std Worked Hours: {:.2f}'.format(std_hours)),
        ], style={'text-align': 'center'})

        fig1 = px.histogram(df_filtered, x='worked_dollars', nbins=num_bins)
        fig1.update_layout(title='Worked Dollars')
        fig2 = px.histogram(df_filtered, x='worked_hours', nbins=num_bins)
        fig2.update_layout(title='Worked Hours')
        fig3 = px.histogram(df_filtered, x='worked_rate', nbins=num_bins)
        fig3.update_layout(title='Worked Rate')
        fig4 = px.histogram(df_filtered, x='timekeeper', nbins=num_bins)
        fig4.update_layout(title='Timekeeper')
        final_div = html.Div([
            html.H1('Worked Dollars'),
            dollars_div,
            dcc.Graph(figure=fig1),
            html.Br(),
            html.H1('Worked Hours'),
            hours_div,
            dcc.Graph(figure=fig2),
            html.Br(),
            html.H1('Worked Rate'),
            dcc.Graph(figure=fig3),
            html.Br(),
            html.H1('Timekeeper'),
            dcc.Graph(figure=fig4)
        ])

        return final_div

    elif tab_value == 'tab-2':
        if flat_fee is None:
            return None
        if profit_margin is None:
            return None
        df_filtered['expected_dollars'] = flat_fee * (1 + profit_margin / 100)
        # build the graph for real worked dollars under current situation
        # and the expected dollars using the set up flat fee with desired
        # profit margin, I want them in bar graphs with 0.5 opacity
        # first build the actual worked dollars graph using the color blue
        # Create histogram for actual worked dollars
        sum_worked_dollars = df_filtered['worked_dollars'].sum()
        sum_expected_dollars = df_filtered['expected_dollars'].sum()
        sum_expected_revenue = df_filtered['expected_dollars'].sum() - \
            df_filtered['worked_dollars'].sum()
        # draw a graph for sum of worked dollars, sum of expected dollars and sum of expected revenue
        fig = go.Figure()
        fig.add_trace(go.Bar(x=['Sum of Worked Dollars', 'Sum of Expected Dollars', 'Sum of Expected Revenue'],
                             y=[sum_worked_dollars, sum_expected_dollars,
                                 sum_expected_revenue],
                             text=[
                                 f'${sum_worked_dollars}', f'${sum_expected_dollars}', f'${sum_expected_revenue}'],
                             textposition='auto',
                             marker_color=['blue', 'orange', 'green'],
                             opacity=0.3))

        # Add the title to the graph
        fig.update_layout(title='Expected Dollars vs Worked Dollars')

        avg_worked_dollars = round(df_filtered['worked_dollars'].mean(), 2)
        avg_expected_dollars = round(df_filtered['expected_dollars'].mean(), 2)
        avg_expected_revenue = round(df_filtered['expected_dollars'].mean() -
                                     df_filtered['worked_dollars'].mean(), 2)
        # draw a graph for average of worked dollars, average of expected dollars and average of expected revenue
        fig_avg = go.Figure()
        fig_avg.add_trace(go.Bar(x=['Average of Worked Dollars', 'Average of Expected Dollars', 'Average of Expected Revenue'],
                                 y=[avg_worked_dollars, avg_expected_dollars,
                                     avg_expected_revenue],
                                 text=[
                                     f'${avg_worked_dollars}', f'${avg_expected_dollars}', f'${avg_expected_revenue}'],
                                 textposition='auto',
                                 marker_color=['blue', 'orange', 'green'],
                                 opacity=0.3))

        # show how many instances we have under the current situation
        instances_num = df_filtered.matter_id.nunique()
        mean_dollar = round(df_filtered['worked_dollars'].mean(), 2)
        std_dollar = round(df_filtered['worked_dollars'].std(), 2)
        result_div = html.Div([
            html.H1('Real Billed Dollars vs Worked Dollars'),
            dcc.Graph(figure=fig),
            html.Br(),
            html.H1('Average Billed Dollars vs Worked Dollars'),
            dcc.Graph(figure=fig_avg),
            html.Br(),
            html.H3(f'Number of Instances: {instances_num}'),
            html.H3(f'Mean Worked Dollars: {mean_dollar}'),
            html.H3(f'Std Worked Dollars: {std_dollar}'),
        ])
        return result_div


if __name__ == '__main__':
    app.run_server(debug=True)
