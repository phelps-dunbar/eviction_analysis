import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from plotly.subplots import make_subplots
from dash import Input, Output, State, html, dcc, dash_table, callback
from openai import OpenAI
import yaml
import json
from scipy import stats


def bar_by_cat(df, metric, agg_func, color=None):
    """
    This function takes in a dataframe, a metric, and an aggregation function and 
    returns a bar chart of the metric by dispute category.
    """
    if color == None:
        df_grouped = df.groupby('dispute_category')[metric].agg(agg_func).\
            reset_index()
    else:
        df_grouped = df.groupby(['dispute_category', color])[metric].agg(agg_func).\
            reset_index()

    df_grouped[metric] = df_grouped[metric].round(2)

    return df_grouped


# define the function creating bar graph with certain design
def bar_trace(df, x_column, y_column, marker, text, orientation='v', hoverinfo='y', textposition='auto'):
    '''
    This function takes in a dataframe, x_column, y_column, orientation, marker, hoverinfo, text, textposition
    and returns a plotly bar graph
    '''
    assert len(df) > 0, 'dataframe must not be empty'
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x_column],
        y=df[y_column],
        orientation=orientation,
        marker=marker,
        hoverinfo=hoverinfo,
        text=text,
        textposition=textposition
    ))
    return fig


def geo_by_cat_graph(df, groupby, metric, agg_func, geojson, thousands=False):
    """
    This function takes in a dataframe, a metric, and an aggregation function and
    returns the grouped info
    """
    assert set(['fips', 'county']).issubset(
        set(df.columns)), 'df must have fips and county columns'
    df_grouped = df.groupby(by=groupby)[metric].agg(agg_func).reset_index()
    if thousands:
        df_grouped[metric] = (df_grouped[metric] / 1000).round(2)
    else:
        df_grouped[metric] = df_grouped[metric].round(2)
    df_num_of_matter = df.groupby(by=groupby)['tmatter'].nunique().\
        reset_index().rename(columns={'tmatter': 'num_of_matter'})
    df_grouped = df_grouped.merge(df[['fips', 'county']].drop_duplicates(),
                                  on='fips', how='left').\
        rename(columns={'county_y': 'county_name'})
    df_grouped = df_grouped.merge(df_num_of_matter, on=groupby, how='left')

    # start building the graph
    if thousands:
        geo_fig = px.choropleth(df_grouped, geojson=geojson,
                                locations='fips', color=metric,
                                hover_name='fips', hover_data=['county', metric, 'num_of_matter'],
                                title=str(agg_func) + '_' + str(metric.capitalize()
                                                                ) + ' by county in Texas, in thousands',
                                color_continuous_scale="Mint")
    else:
        geo_fig = px.choropleth(df_grouped, geojson=geojson,
                                locations='fips', color=metric,
                                hover_name='fips', hover_data=['county', metric, 'num_of_matter'],
                                title=str(
                                    agg_func) + '_' + str(metric.capitalize()) + ' by county in Texas',
                                color_continuous_scale="Mint")

    geo_fig.update_layout(height=600)
    geo_fig.update_geos(showcountries=False, showcoastlines=True, showland=True,
                        fitbounds="locations", scope="usa", center={"lat": 31.9686, "lon": -99.9018}
                        )

    return geo_fig

    ########################## HERE ARE THE FUNCTION FOR EACH DASHBOARD TABS ##############################


def flat_fee_graph(df_profit, expected_profit_margin):
    # assign correct values into these values
    avg_amt_billed = round(df_profit['total_amount_billed'].mean(), 2)
    avg_cost_billed = round(df_profit['total_cost_billed'].mean(), 2)
    number_of_instances = df_profit['matter_id'].nunique()
    profit_margin = round(
        (avg_amt_billed - avg_cost_billed) / avg_amt_billed, 2)
    num_of_matters = df_profit['tmatter'].nunique()
    headline = 'The number of matters under current selection is ' + \
        str(num_of_matters)

    if expected_profit_margin is None:
        return html.Div(html.H1(headline)), None, None

    else:
        # calculate the expected fee using the cost and expected profit margin
        flat_fee = round(avg_cost_billed * (1 + expected_profit_margin), 2)
        data = [
            {"avg_amt_billed": avg_amt_billed, "avg_cost_billed": avg_cost_billed,
             "profit_margin_percent": str(profit_margin * 100) + '%',
             "number_of_instances": number_of_instances, "flat_fee": flat_fee,
             "current_average_profit_margin": str(profit_margin * 100) + '%', }
        ]
        data = pd.DataFrame(data)
        data = dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{"name": i, "id": i} for i in data.columns]
        )

        return html.Div(html.H1(headline)), None, data


########################################################## time graph function ##########################################################
def mopen_graph(grouped_df, selected_client, df_elite_raw, df_cost_raw):
    fig = px.bar(grouped_df, x='year_month', y='counts', color='dispute_category',
                 title='Number of matters by dispute category over time',
                 text='counts',
                 labels={'year_month': 'Year-Month', 'counts': 'Number of matters'})
    fig.update_layout(height=600)

    # generate a plotly figure for billed amount(tbilldol) by time(tworkdt)
    # having different status(tstatus) by color
    if selected_client == None:
        df = df_elite_raw.copy()
    else:
        df = df_elite_raw.loc[df_elite_raw['tmatter'].str[:5]
                              == selected_client, :].copy()
    # group by year_month and tstatus, then sum the tbilldol column
    df_monthly = df.groupby(['work_year_month', 'tstatus'])['tworkdol'].\
        sum().reset_index()

    # create the billed amount by time graph
    billed_fig = px.bar(df_monthly, x='work_year_month', y='tworkdol',
                        color='tstatus', title='Billed Amount by Time',
                        text='tworkdol',
                        labels={'work_year_month': 'Time',
                                'tworkdol': 'Billed Amount'},
                        height=600,
                        color_discrete_sequence=px.colors.sequential.Plasma_r)  # change color scheme
    billed_fig.update_layout(
        barmode='stack',
        plot_bgcolor='rgb(230, 230,230)',
        xaxis=dict(
            title='Time',
            color='gray',
            showgrid=True,
            gridcolor='lightgrey',
        ),
        yaxis=dict(
            title='Billed Amount ($)',
            color='gray',
            showgrid=True,
            gridcolor='lightgrey',
        ),
        legend=dict(
            font_size=10,
            yanchor="top",
            y=0.99,
            xanchor="center",
            x=0.50
        ),
        font=dict(
            size=12
        )
    )

    # generate a plotly figure for billed amount(tbilldol) by time(tworkdt)
    # having different status(tstatus) by color
    if selected_client == None:
        df = df_cost_raw.copy()
    else:
        df = df_cost_raw.loc[df_cost_raw['matter_id'].str[:5]
                             == selected_client, :].copy()
    num_of_matters = df['matter_id'].nunique()

    # generate the year_month column for df_elite_raw
    df['date_billed'] = pd.to_datetime(df['date_billed'])
    df['work_year_month'] = df['date_billed'].dt.to_period('M').astype(str)
    df['work_year_month'] = pd.to_datetime(df['work_year_month'])
    df_monthly = df.groupby(['work_year_month', 'status_code'])['amount_billed'].\
        sum().reset_index()

    # create the cost amount by time graph
    # round the amount_billed column to 2 decimal places
    df_monthly['amount_billed'] = df_monthly['amount_billed'].round(2)
    cost_fig = px.bar(df_monthly, x='work_year_month', y='amount_billed',
                      color='status_code', title='Cost Amount by Time',
                      text='amount_billed',
                      labels={'work_year_month': 'Time',
                              'amount_billed': 'Cost Amount'},
                      height=600,
                      color_discrete_sequence=px.colors.sequential.Plasma_r)
    cost_fig.update_layout(
        barmode='stack',
        plot_bgcolor='rgb(230, 230,230)',
        xaxis=dict(
            title='Time',
            color='gray',
            showgrid=True,
            gridcolor='lightgrey',
        ),
        yaxis=dict(
            title='Cost Amount ($)',
            color='gray',
            showgrid=True,
            gridcolor='lightgrey',
        ),
        legend=dict(
            font_size=10,
            yanchor="top",
            y=0.99,
            xanchor="center",
            x=0.50
        ),
        font=dict(
            size=12
        )
    )

    headline = 'The number of matters under current selection is ' + \
        str(num_of_matters)

    return html.Div(children=[html.H1(headline)]), html.Div([
        html.Div([html.A('Go to Timeline', href='#time-section'),
                  html.A('Go to Billed Amount', href='#billed-amount-section'),
                  html.A('Go to Cost Amount', href='#cost-amount-section'),
                  ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='time-section', children=[
            html.H3('Matter Open Date by Dispute Category'),
            dcc.Graph(figure=fig)
        ]),
        html.Br(),
        html.Div(id='billed-amount-section', children=[
            html.H3('Billed Amount by Time'),
            dcc.Graph(figure=billed_fig)
        ]),
        html.Br(),
        html.Div(id='cost-amount-section', children=[
            html.H3('Cost Amount by Time'),
            dcc.Graph(figure=cost_fig)
        ]),
    ]), None


########################################################## total hours graph function ##########################################################
def hr_worked_graph(selected_client, df_profit, df_hours_by_level, filtered_counties):
    # first, need to remove the outliers for the df_hours_by_level
    # an outlier is defined as 'hours_worked' not in the middle 80% interval
    # of the 'hours_worked' column under current df_hours_by_level
    # calculate the 10th and 90th percentile of the 'hours_worked' column
    lower_bound = df_hours_by_level['hours_worked'].quantile(0.1)
    upper_bound = df_hours_by_level['hours_worked'].quantile(0.9)
    # remove the outliers
    df_hours_by_level = df_hours_by_level.loc[(df_hours_by_level['hours_worked'] >= lower_bound) &
                                              (df_hours_by_level['hours_worked'] <= upper_bound), :]

    hover_data = {'total_hours_worked': True,
                  'client_name': False, 'dispute_category': False}
    total_hrs_worked_df = bar_by_cat(
        df_profit, 'total_hours_worked', 'sum', color='client_name')
    avg_hrs_worked_df = bar_by_cat(
        df_profit, 'total_hours_worked', 'mean', color='client_name')
    total_hrs_worked_by_levels_df = df_hours_by_level.groupby('tk_title')['hours_worked'].\
        sum().reset_index().sort_values('hours_worked', ascending=False)
    total_hrs_worked_by_levels_df['hours_worked'] = total_hrs_worked_by_levels_df['hours_worked'].round(
        2)
    total_hrs_worked_by_levels_df = total_hrs_worked_by_levels_df.rename(
        columns={'hours_worked': 'total_hours_worked'})
    avg_hrs_worked_by_levels_df = df_hours_by_level.groupby('tk_title')['hours_worked'].\
        mean().reset_index().sort_values('hours_worked', ascending=False)
    avg_hrs_worked_by_levels_df = avg_hrs_worked_by_levels_df.rename(
        columns={'hours_worked': 'avg_hours_worked'})
    avg_hrs_worked_by_levels_df['avg_hours_worked'] = avg_hrs_worked_by_levels_df['avg_hours_worked'].round(
        2)
    avg_hrs_worked_df = avg_hrs_worked_df.rename(
        columns={'total_hours_worked': 'avg_hours_worked'})
    total_hrs_worked_fig = px.bar(total_hrs_worked_df, x='total_hours_worked',
                                  y='dispute_category', orientation='h', color='client_name',
                                  text='total_hours_worked', hover_data=hover_data, title='Total Hours Worked by Client')
    total_hrs_by_level_fig = px.bar(total_hrs_worked_by_levels_df, x='tk_title', y='total_hours_worked', color='tk_title',
                                    orientation='v', hover_data={'total_hours_worked': True, 'tk_title': False},
                                    text_auto=True, title='Total Hours Worked by Levels')
    total_hrs_by_level_fig.update_layout(
        xaxis={'categoryorder': 'total descending'})
    avg_hrs_worked_fig = px.bar(avg_hrs_worked_df, x='avg_hours_worked',
                                y='dispute_category', orientation='h', color='client_name',
                                text='avg_hours_worked', text_auto=True, title='Average Hours Worked by Client',
                                hover_data={'avg_hours_worked': True, 'client_name': False, 'dispute_category': False})
    avg_hrs_by_level_fig = px.bar(avg_hrs_worked_by_levels_df, x='tk_title', y='avg_hours_worked', color='tk_title',
                                  orientation='v', hover_data={'avg_hours_worked': True, 'tk_title': False},
                                  text_auto=True, title='Average Hours Worked by Levels')
    avg_hrs_by_level_fig.update_layout(
        xaxis={'categoryorder': 'total descending'})
    df_hours_by_level = df_hours_by_level.sort_values('matter_id')
    hrs_by_level_by_matter_fig = px.bar(df_hours_by_level, x='matter_id', y='hours_worked', color='tk_title',
                                        hover_data={
                                            'hours_worked': True, 'matter_id': 'category', 'category': False},
                                        text_auto=True, title='Hours Worked by Levels by Matter')
    hrs_by_level_by_matter_fig.update_layout(barmode='stack', xaxis={
                                             'categoryorder': 'array', 'categoryarray': df_hours_by_level['matter_id']})

    # configure a bar graph x axis being each matter, I want to show the difference between
    # the the actual amounts billed versus standard_rate_amount to see how much discount
    # we are currently providing for each matter for each tk_title level, so each matter
    # shall have two bars, first one being the amounts billed, second one being the standard_rate_amount
    cost_by_level_by_matter_fig = make_subplots(rows=1, cols=2)

    # Define bar plots for each title
    for title in df_hours_by_level['tk_title'].unique():
        df_subset = df_hours_by_level[df_hours_by_level['tk_title'] == title]
        df_subset = df_subset.sort_values('matter_id')
        # sort df_subset by matter_id

        cost_by_level_by_matter_fig.add_trace(
            go.Bar(x=df_subset['matter_id'],
                   y=df_subset['amounts_billed'], name=title),
            row=1, col=1
        )
        cost_by_level_by_matter_fig.add_trace(
            go.Bar(x=df_subset['matter_id'],
                   y=df_subset['standard_rate_amount'], name=title),
            row=1, col=2
        )

    cost_by_level_by_matter_fig.update_layout(title_text="Actual Amount Billed vs Standard Rate Amount by Matter",
                                              xaxis={'categoryorder': 'array', 'categoryarray': df_subset['matter_id']})

    # configure histograms, one for each tk_title under current df_hours_by_level
    # create a list of tk_title

    tk_title_list = df_hours_by_level['tk_title'].unique().tolist()
    # create a list of histogram figures
    hist_fig_list = []
    for tk_title in tk_title_list:
        df = df_hours_by_level.loc[df_hours_by_level['tk_title']
                                   == tk_title, :]
        fig = px.histogram(df, x='hours_worked', nbins=20,
                           title=f'Histogram of Hours Worked for {tk_title}')
        hist_fig_list.append(fig)

    total_hr = round(df_profit['total_hours_worked'].sum(), 2)
    avg_hr = round(df_profit['total_hours_worked'].mean(), 2)
    num_of_matters = df_hours_by_level['matter_id'].nunique()

    # add marker lines between each bar for better distinction
    total_hrs_worked_fig.update_traces(marker_line_color='darkgray',
                                       marker_line_width=1.5)

    total_hrs_worked_fig.update_layout(
        title='Total Hours Worked by Client',
        xaxis_title='Total Hours Worked',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    avg_hrs_worked_fig.update_traces(marker_line_color='darkgray',
                                     marker_line_width=1.5)
    avg_hrs_worked_fig.update_layout(
        title='Average Hours Worked by Client',
        xaxis_title='Average Hours Worked',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    # the geographical graph
    # Compute total_worked_hrs for each county
    geo_fig = geo_by_cat_graph(df_profit, 'fips', 'total_hours_worked', 'mean',
                               geojson=filtered_counties)
    geo_fig_2 = geo_by_cat_graph(df_profit, 'fips', 'total_hours_worked', 'sum',
                                 geojson=filtered_counties)

    # define the headline depending on whether a client is selected
    if selected_client == None:
        headline2 = 'The total hours worked is ' + str(total_hr) + ' hours.'
        headline1 = 'The average hours worked per matter is ' + \
            str(avg_hr) + ' hours.'

    else:
        headline2 = 'The total hours worked for Client ' + str(selected_client) + \
            ' is ' + str(total_hr) + ' hours.'
        headline1 = 'The average hours worked per matter for Client ' + str(selected_client) + \
            ' is ' + str(avg_hr) + ' hours.'
    headline3 = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline3)), html.Div(children=[
        html.Div([
            html.A('Go to Average', href='#average-section'),
            html.A('Go to Total', href='#total-section'),
            html.A('Go to Hrs by Levels', href='#hrs-by-levels-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='average-section', children=[
            html.H2(headline1),
            dcc.Graph(figure=avg_hrs_worked_fig),
            dcc.Graph(figure=geo_fig)
        ]),
        html.Br(),
        html.Div(id='total-section', children=[
            html.H2(headline2),
            dcc.Graph(figure=total_hrs_worked_fig),
            dcc.Graph(figure=geo_fig_2)
        ]),
        html.Br(),
        html.Div(id='hrs-by-levels-section', children=[
            html.Div(children=[
                dcc.Graph(figure=hrs_by_level_by_matter_fig,
                          style={'width': '70%', 'display': 'inline-block'}),
                dcc.Graph(figure=avg_hrs_by_level_fig,
                          style={'width': '30%', 'display': 'inline-block'}),]),
            html.Div(children=[
                dcc.Graph(figure=cost_by_level_by_matter_fig,
                          style={'width': '70%', 'display': 'inline-block'}),
                dcc.Graph(figure=total_hrs_by_level_fig,
                          style={'width': '30%', 'display': 'inline-block'})]),
            html.Div(children=[dcc.Graph(id=f'graph-{i}',
                                         figure=fig) for i, fig in enumerate(hist_fig_list)])
        ]),
    ]), None


########################################################## amount billed graph function ##########################################################
def amt_billed_graph(selected_client, df_elite, df_profit, filtered_counties, client_color_discrete_map, num_of_matters):
    if selected_client == None:
        total_hover_data = {'total_amount_billed': True,
                            'client_name': False, 'dispute_category': False}
        avg_hover_data = {'avg_amount_billed': True,
                          'client_name': False, 'dispute_category': False}
        total_amt_billed_df = bar_by_cat(
            df_elite, 'total_amount_billed', 'sum', color='client_name')
        avg_amt_billed_df = bar_by_cat(
            df_elite, 'total_amount_billed', 'mean', color='client_name')
        avg_amt_billed_df = avg_amt_billed_df.rename(
            columns={'total_amount_billed': 'avg_amount_billed'})
        total_amt_billed_fig = px.bar(total_amt_billed_df, x='total_amount_billed',
                                      y='dispute_category', orientation='h', color='client_name',
                                      color_discrete_map=client_color_discrete_map,
                                      hover_data=total_hover_data, text='total_amount_billed')
        avg_amt_billed_fig = px.bar(avg_amt_billed_df, x='avg_amount_billed',
                                    y='dispute_category', orientation='h', color='client_name',
                                    color_discrete_map=client_color_discrete_map,
                                    hover_data=avg_hover_data, text='avg_amount_billed')
        num_of_matters = df_elite['tmatter'].nunique()

    else:
        total_hover_data = {'total_amount_billed': True,
                            'dispute_category': False}
        avg_hover_data = {'avg_amount_billed': True, 'dispute_category': False}
        total_amt_billed_df = bar_by_cat(
            df_profit, 'total_amount_billed', 'sum')
        avg_amt_billed_df = bar_by_cat(
            df_profit, 'total_amount_billed', 'mean')
        avg_amt_billed_df = avg_amt_billed_df.rename(
            columns={'total_amount_billed': 'avg_amount_billed'})
        total_amt_billed_fig = px.bar(total_amt_billed_df, x='total_amount_billed',
                                      y='dispute_category', orientation='h',
                                      hover_data=total_hover_data, text='total_amount_billed')
        avg_amt_billed_fig = px.bar(avg_amt_billed_df, x='avg_amount_billed',
                                    y='dispute_category', orientation='h',
                                    hover_data=avg_hover_data, text='avg_amount_billed')
        num_of_matters = df_profit['tmatter'].nunique()

    # add marker lines between each bar for better distinction
    total_amt_billed_fig.update_traces(marker_line_color='darkgray',
                                       marker_line_width=1.5)
    total_amt_billed_fig.update_layout(
        title='Total Amount Billed by Client',
        xaxis_title='Total Amount Billed',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    avg_amt_billed_fig.update_traces(marker_line_color='darkgray',
                                     marker_line_width=1.5)
    avg_amt_billed_fig.update_layout(
        title='Average Amount Billed by Client',
        xaxis_title='Average Amount Billed',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    # the geographical graph
    # Compute total_amount_billed for each county
    df_elite_2 = df_elite.rename(
        columns={'total_amount_billed': 'avg_amount_billed'})
    geo_fig = geo_by_cat_graph(df_elite_2, 'fips', 'avg_amount_billed', 'mean',
                               geojson=filtered_counties, thousands=True)
    geo_fig_2 = geo_by_cat_graph(df_elite, 'fips', 'tmatter', 'nunique',
                                 geojson=filtered_counties, thousands=False)
    geo_fig_3 = geo_by_cat_graph(df_elite, 'fips', 'total_amount_billed', 'sum',
                                 geojson=filtered_counties, thousands=True)

    # define the headline depending on whether a client is selected
    if selected_client == None:
        total_amt_billed = round(df_elite['total_amount_billed'].sum(), 2)
        avg_amt_billed = round(df_elite['total_amount_billed'].mean(), 2)
        headline3 = 'The total amount billed is ' + \
            str(total_amt_billed) + ' dollars.'
        headline1 = 'The average amount billed per matter is ' + \
            str(avg_amt_billed) + ' dollars.'
        headline2 = 'The number of matters is ' + str(num_of_matters) + '.'
    else:
        total_amt_billed = round(df_profit['total_amount_billed'].sum(), 2)
        avg_amt_billed = round(df_profit['total_amount_billed'].mean(), 2)
        client_num_of_matters = df_profit['tmatter'].nunique()
        headline3 = 'The total amount billed for Client ' + str(selected_client) + \
            ' is ' + str(total_amt_billed) + ' dollars.'
        headline1 = 'The average amount billed per matter for Client ' + str(selected_client) + \
            ' is ' + str(avg_amt_billed) + ' dollars.'
        headline2 = 'The number of matters for Client ' + str(selected_client) + \
            ' is ' + str(client_num_of_matters) + '.'
    headline4 = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline4)), html.Div(children=[
        html.Div([
            html.A('Go to Average', href='#average-section'),
            html.A('Go to Counts', href='#counts-section'),
            html.A('Go to Total', href='#total-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='average-section', children=[
            html.H2(headline1),
            dcc.Graph(figure=avg_amt_billed_fig),
            dcc.Graph(figure=geo_fig)
        ]),
        html.Br(),
        html.Div(id='counts-section', children=[
            html.H2(headline2),
            dcc.Graph(figure=geo_fig_2)
        ]),
        html.Br(),
        html.Div(id='total-section', children=[
            html.H2(headline3),
            dcc.Graph(figure=total_amt_billed_fig),
            dcc.Graph(figure=geo_fig_3)
        ]),
    ]), None


########################################################## number of timekeepers graph function ##########################################################
def num_of_tks_graph(selected_client, df_profit, df_elite, filtered_counties, client_color_discrete_map):
    if selected_client == None:
        avg_tks = round(df_elite['number_of_timekeepers'].mean(), 2)
        hover_data = {'number_of_timekeepers': True,
                      'client_name': False, 'dispute_category': False}
        avg_num_tks_df = bar_by_cat(df_elite, 'number_of_timekeepers', 'mean',
                                    color='client_name')
        avg_num_tks_fig = px.bar(avg_num_tks_df, x='number_of_timekeepers',
                                 y='dispute_category', orientation='h', color='client_name',
                                 color_discrete_map=client_color_discrete_map,
                                 hover_data=hover_data, text='number_of_timekeepers')
        num_of_matters = df_elite['tmatter'].nunique()

    else:
        avg_tks = round(df_profit['number_of_timekeepers'].mean(), 2)
        hover_data = {'number_of_timekeepers': True, 'dispute_category': False}
        avg_num_tks_df = bar_by_cat(df_profit, 'number_of_timekeepers', 'mean')
        avg_num_tks_fig = px.bar(avg_num_tks_df, x='number_of_timekeepers',
                                 y='dispute_category', orientation='h',
                                 hover_data=hover_data, text='number_of_timekeepers')
        num_of_matters = df_profit['tmatter'].nunique()

    # add marker lines between each bar for better distinction
    avg_num_tks_fig.update_traces(marker_line_color='darkgray',
                                  marker_line_width=1.5)
    avg_num_tks_fig.update_layout(
        title='Average Number of Tks by Client',
        xaxis_title='Average Number of Timekeepers',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    # the geographical graph
    # Compute total_worked_hrs for each county
    if selected_client == None:
        geo_fig = geo_by_cat_graph(df_elite, 'fips', 'number_of_timekeepers', 'mean',
                                   geojson=filtered_counties)
        headline = 'The average number of timekeepers for all matters ' + \
            str(avg_tks) + ' people.'
    else:
        geo_fig = geo_by_cat_graph(df_profit, 'fips', 'number_of_timekeepers', 'mean',
                                   geojson=filtered_counties)
        headline = 'The average number of timekeepers for Client ' + str(selected_client) + \
            ' is ' + str(avg_tks) + ' people.'
    headline2 = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline2)), html.Div(children=[
        html.Div([
            html.A('Go to Average', href='#average-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='average-section', children=[
            html.H2(headline),
            dcc.Graph(figure=avg_num_tks_fig),
            html.Br(),
            dcc.Graph(figure=geo_fig)
        ])
    ]), None

########################################################## time taken graph function ##########################################################


def time_taken_graph(selected_client, df_profit, df_elite, filtered_counties, client_color_discrete_map):
    if selected_client == None:
        avg_time_taken = round(df_elite['time_taken'].mean(), 2)
        std_time_taken = round(df_elite['time_taken'].std(), 2)
        # add a histogram for time_taken
        time_taken_hist = px.histogram(df_elite, x='time_taken', range_x=[0, max(df_elite['time_taken'])],
                                       nbins=20, labels={'time_taken': 'Time Taken (days)'},
                                       color='client_name', opacity=0.7)
        hover_data = {'time_taken': True,
                      'client_name': False, 'dispute_category': False}
        avg_time_taken_df = bar_by_cat(
            df_elite, 'time_taken', 'mean', color='client_name')
        avg_time_taken_fig = px.bar(avg_time_taken_df, x='time_taken',
                                    y='dispute_category', orientation='h', color='client_name',
                                    color_discrete_map=client_color_discrete_map,
                                    text=avg_time_taken_df['time_taken'],
                                    hover_data=hover_data)
        num_of_matters = df_elite['tmatter'].nunique()

    else:
        avg_time_taken = round(df_profit['time_taken'].mean(), 2)
        std_time_taken = round(df_profit['time_taken'].std(), 2)
        # add a histogram for time_taken
        time_taken_hist = px.histogram(df_profit, x='time_taken', range_x=[0, max(df_profit['time_taken'])],
                                       nbins=20, labels={'time_taken': 'Time Taken (days)'},
                                       opacity=0.7)
        hover_data = {'time_taken': True, 'dispute_category': False}
        avg_time_taken_df = bar_by_cat(df_profit, 'time_taken', 'mean')
        avg_time_taken_fig = px.bar(avg_time_taken_df, x='time_taken',
                                    y='dispute_category', orientation='h',
                                    text=avg_time_taken_df['time_taken'],
                                    hover_data=hover_data)
        num_of_matters = df_profit['tmatter'].nunique()

    # add marker lines between each bar for better distinction
    avg_time_taken_fig.update_traces(marker_line_color='darkgray',
                                     marker_line_width=1.5)
    avg_time_taken_fig.update_layout(
        title='Average Time Taken by Client',
        xaxis_title='Average Time Taken',
        yaxis_title='Client',
        yaxis={'categoryorder': 'total ascending'},
        height=600)

    time_taken_hist.update_layout(
        title_text='Histogram of Time Taken',
        xaxis_title_text='Time Taken (days)',
        yaxis_title_text='Count',
        font=dict(
            size=14,
        ),
        margin=dict(l=20, r=20, t=40, b=20))

    # the geographical graph
    # Compute total_worked_hrs for each county
    if selected_client == None:
        geo_fig = geo_by_cat_graph(df_elite, 'fips', 'time_taken', 'mean',
                                   geojson=filtered_counties)
        headline1 = 'The average time taken for all matters is ' + \
            str(avg_time_taken) + ' days.'
        headline2 = 'The standard deviation of time taken for all matters is ' + \
            str(std_time_taken) + ' days.'
    else:
        geo_fig = geo_by_cat_graph(df_profit, 'fips', 'time_taken', 'mean',
                                   geojson=filtered_counties)
        headline1 = 'The average time taken for Client ' + str(selected_client) + \
            ' is ' + str(avg_time_taken) + ' days.'
        headline2 = 'The standard deviation of time taken for Client ' + str(selected_client) + \
            ' is ' + str(std_time_taken) + ' days.'
    headline3 = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline3)), html.Div(children=[
        html.Div([
            html.A('Go to Average', href='#average-section'),
            html.A('Go to Histogram', href='#histogram-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='average-section', children=[
            html.H2(headline1),
            dcc.Graph(figure=avg_time_taken_fig),
            dcc.Graph(figure=geo_fig)
        ]),
        html.Br(),
        html.Div(id='histogram-section', children=[
            html.H2(headline2),
            dcc.Graph(figure=time_taken_hist)
        ]),
    ]), None

########################################################## cost graph function ##########################################################


def cost_graph(df_profit, filtered_counties):
    avg_cost = round(df_profit['total_cost_billed'].mean(), 2)
    total_cost = round(df_profit['total_cost_billed'].sum(), 2)

    # Configuring the bar
    avg_cost_df = bar_by_cat(df_profit, 'total_cost_billed', 'mean')
    marker = {'color': avg_cost_df['total_cost_billed'], 'colorscale': 'Blues', 'line': {
        'color': 'darkgray', 'width': 1.5}}
    avg_cost_fig = bar_trace(avg_cost_df, 'total_cost_billed', 'dispute_category',
                             marker, text=avg_cost_df['total_cost_billed'], orientation='h', hoverinfo='x')

    # Updating layout
    avg_cost_fig.update_layout(
        title={'text': 'Average Cost by Dispute Category',
               'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title='Average Cost',
        yaxis_title='Dispute Category',
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        plot_bgcolor='#F0F0F0',
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )

    total_cost_df = bar_by_cat(df_profit, 'total_cost_billed', 'sum')
    marker = {'color': total_cost_df['total_cost_billed'], 'colorscale': 'Blues', 'line': {
        'color': 'darkgray', 'width': 1.5}}
    total_cost_fig = bar_trace(total_cost_df, 'total_cost_billed', 'dispute_category',
                               marker, text=total_cost_df['total_cost_billed'], orientation='h', hoverinfo='x')

    # update the layout
    total_cost_fig.update_layout(
        title={'text': 'Total Cost by Dispute Category',
               'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title='Total Cost',
        yaxis_title='Dispute Category',
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        plot_bgcolor='#F0F0F0',
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )

    avg_cost_geo_fig = geo_by_cat_graph(df_profit, 'fips', 'total_cost_billed', 'mean',
                                        geojson=filtered_counties)
    total_cost_geo_fig = geo_by_cat_graph(df_profit, 'fips', 'total_cost_billed', 'sum',
                                          geojson=filtered_counties)

    num_of_matters = df_profit['tmatter'].nunique()
    headline = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline)), html.Div(children=[
        html.Div([
            html.A('Go to Average', href='#average-section'),
            html.A('Go to Total', href='#total-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        html.Div(id='average-section', children=[
            html.H2('The average cost is ' +
                    str(avg_cost) + ' dollars per matter.'),
            dcc.Graph(figure=avg_cost_fig),
            dcc.Graph(figure=avg_cost_geo_fig)
        ]),
        html.Br(),
        html.Div(id='total-section', children=[
            html.H2('The total cost is ' + str(total_cost) + ' dollars.'),
            dcc.Graph(figure=total_cost_fig),
            dcc.Graph(figure=total_cost_geo_fig)
        ]),
    ]), None

########################################################## profit graph function ##########################################################


def profit_graph(df_profit, filtered_counties):
    # first, generate the profit column
    df_profit['profit'] = df_profit['total_amount_billed'] - \
        df_profit['total_cost_billed']
    # then generate the profit ratio
    df_profit['profit_ratio'] = df_profit['profit'] / \
        df_profit['total_amount_billed']
    # then generate the rate of return
    df_profit['rate_of_return'] = df_profit['profit'] / \
        df_profit['total_cost_billed']

    # generate the average profit, average profit ratio and average rate of return
    avg_profit = round(df_profit['profit'].mean(), 2)
    avg_profit_ratio = round(df_profit['profit_ratio'].mean(), 2)
    df_profit_have_cost = df_profit[df_profit['total_cost_billed'] != 0]
    avg_rate_of_return = round(df_profit_have_cost['rate_of_return'].mean(), 2)

    # configure a bar chart for average profit
    avg_profit_df = bar_by_cat(df_profit, 'profit', 'mean')
    marker = {'color': avg_profit_df['profit'], 'colorscale': 'Blues', 'line': {
        'color': 'darkgray', 'width': 1.5}}
    avg_profit_fig = bar_trace(avg_profit_df, 'profit', 'dispute_category', marker,
                               text=avg_profit_df['profit'], orientation='h', hoverinfo='x')

    # update the layout
    avg_profit_fig.update_layout(
        title={'text': 'Average Profit by Dispute Category',
               'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title='Average Profit',
        yaxis_title='Dispute Category',
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        plot_bgcolor='#F0F0F0',
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )

    # configure a bar chart for average profit ratio
    avg_profit_ratio_df = bar_by_cat(df_profit, 'profit_ratio', 'mean')
    marker = {'color': avg_profit_ratio_df['profit_ratio'], 'colorscale': 'Blues', 'line': {
        'color': 'darkgray', 'width': 1.5}}
    avg_profit_ratio_fig = bar_trace(avg_profit_ratio_df, 'profit_ratio', 'dispute_category', marker,
                                     text=avg_profit_ratio_df['profit_ratio'], orientation='h', hoverinfo='x')

    # update the layout
    avg_profit_ratio_fig.update_layout(
        title={'text': 'Average Profit Ratio by Dispute Category',
               'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title='Average Profit Ratio',
        yaxis_title='Dispute Category',
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        plot_bgcolor='#F0F0F0',
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )

    # as for rate of return, neglect the ones without any cost
    df_profit = df_profit[df_profit['total_cost_billed'] != 0]

    # configure a bar chart for average rate of return
    avg_rate_of_return_df = bar_by_cat(df_profit, 'rate_of_return', 'mean')
    marker = {'color': avg_rate_of_return_df['rate_of_return'],
              'colorscale': 'Blues', 'line': {'color': 'darkgray', 'width': 1.5}}

    avg_rate_of_return_fig = bar_trace(avg_rate_of_return_df, 'rate_of_return',
                                       'dispute_category', marker,
                                       text=avg_rate_of_return_df['rate_of_return'],
                                       orientation='h', hoverinfo='x')
    # update the layout
    avg_rate_of_return_fig.update_layout(
        title={'text': 'Average Rate of Return by Dispute Category',
               'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title='Average Rate of Return',
        yaxis_title='Dispute Category',
        yaxis={'categoryorder': 'total ascending'},
        height=600,
        plot_bgcolor='#F0F0F0',
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )

    # generate the geographical graph
    avg_profit_geo_fig = geo_by_cat_graph(df_profit, 'fips', 'profit', 'mean',
                                          geojson=filtered_counties)
    avg_profit_ratio_geo_fig = geo_by_cat_graph(df_profit, 'fips', 'profit_ratio', 'mean',
                                                geojson=filtered_counties)
    avg_rate_of_return_geo_fig = geo_by_cat_graph(df_profit, 'fips', 'rate_of_return', 'mean',
                                                  geojson=filtered_counties)

    num_of_matters = df_profit['tmatter'].nunique()
    headline = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline)), html.Div(children=[
        html.Div([
            html.A('Go to Average Profit', href='#average-profit-section'),
            html.A('Go to Average Profit Ratio',
                   href='#average-profit-ratio-section'),
            html.A('Go to Average Rate of Return',
                   href='#average-rate-of-return-section'),
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),

        html.Div(id='average-profit-section', children=[
            html.H2('The average profit is ' +
                    str(avg_profit) + ' dollars per matter.'),
            dcc.Graph(figure=avg_profit_fig),
            dcc.Graph(figure=avg_profit_geo_fig)
        ]),
        html.Br(),

        html.Div(id='average-profit-ratio-section', children=[
            html.H2('The average profit ratio is ' +
                    str(avg_profit_ratio) + '.'),
            dcc.Graph(figure=avg_profit_ratio_fig),
            dcc.Graph(figure=avg_profit_ratio_geo_fig)
        ]),
        html.Br(),

        html.Div(id='average-rate-of-return-section', children=[
            html.H2('The average rate of return is ' +
                    str(avg_rate_of_return) + '.'),
            dcc.Graph(figure=avg_rate_of_return_fig),
            dcc.Graph(figure=avg_rate_of_return_geo_fig)
        ]),
    ]), None


####################################################### Hrs function#######################################################
def hrs_graph(selected_department, selected_location):
    hrs_df = pd.read_csv('work_by_hours.csv')
    hrs_df['worked_hours'] = round(hrs_df['worked_hours'], 2)

    if selected_department and selected_location:
        selected_df = hrs_df.loc[hrs_df['department'].isin(
            selected_department) & hrs_df['location'].isin(selected_location), :]
    elif selected_department and not selected_location:
        selected_df = hrs_df.loc[hrs_df['department'].isin(
            selected_department)]
    elif selected_location and not selected_department:
        selected_df = hrs_df.loc[hrs_df['location'].isin(selected_location)]
    else:
        selected_df = hrs_df
    num_of_matters = selected_df['matter_id'].nunique()

    # configure a bar chart for total worked hours by title for each client
    sum_worked_hours_df = selected_df.groupby(
        'Title')['worked_hours'].sum().reset_index()
    sum_worked_hours_df = sum_worked_hours_df.sort_values(
        by='worked_hours', ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=selected_df['Title'],
        y=selected_df['worked_hours'],
        name='Total Hours Worked',
        marker_color='lightsalmon',
        text=selected_df['worked_hours'],
        textposition='auto'
    ))

    # configure the average worked hours by title for each client
    avg_worked_hours_df = selected_df.groupby(
        'Title')['worked_hours'].mean().reset_index()
    # round the average worked hours to 2 decimal places
    avg_worked_hours_df['worked_hours'] = round(
        avg_worked_hours_df['worked_hours'], 2)
    avg_worked_hours_df = avg_worked_hours_df.sort_values(
        by='worked_hours', ascending=False)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=avg_worked_hours_df['Title'],
        y=avg_worked_hours_df['worked_hours'],
        name='Average Hours Worked',
        marker_color='lightsalmon',
        text=avg_worked_hours_df['worked_hours'],
        textposition='auto'
    ))

    # configure the total potential lost for each client by title
    lost_amount_df = selected_df.groupby(
        'Title')['profit_lost'].sum().reset_index()
    # round the total potential lost to 2 decimal places
    lost_amount_df['profit_lost'] = round(lost_amount_df['profit_lost'], 2)
    lost_amount_df = lost_amount_df.sort_values(
        by='profit_lost', ascending=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=lost_amount_df['Title'],
        y=lost_amount_df['profit_lost'],
        name='Total Potential Lost',
        marker_color='lightsalmon',
        text=lost_amount_df['profit_lost'],
        textposition='auto'))

    # configure the average potential lost for each client by title
    avg_lost_amount_df = selected_df.groupby(
        'Title')['profit_lost'].mean().reset_index()
    # round the average potential lost to 2 decimal places
    avg_lost_amount_df['profit_lost'] = round(
        avg_lost_amount_df['profit_lost'], 2)
    avg_lost_amount_df = avg_lost_amount_df.sort_values(
        by='profit_lost', ascending=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=avg_lost_amount_df['Title'],
        y=avg_lost_amount_df['profit_lost'],
        name='Average Potential Lost',
        marker_color='lightsalmon',
        text=avg_lost_amount_df['profit_lost'],
        textposition='auto'))

    # configure the total lost hours for each client by title due to worked_hours not billed
    sum_hours_lost_df = selected_df.groupby(
        'Title')['hours_lost'].sum().reset_index()
    # round the total lost hours to 2 decimal places
    sum_hours_lost_df['hours_lost'] = round(sum_hours_lost_df['hours_lost'], 2)
    sum_hours_lost_df = sum_hours_lost_df.sort_values(
        by='hours_lost', ascending=False)
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=sum_hours_lost_df['Title'],
        y=sum_hours_lost_df['hours_lost'],
        name='Total Lost Hours',
        marker_color='lightsalmon',
        text=sum_hours_lost_df['hours_lost'],
        textposition='auto'))

    # configure the average lost hours for each client by title due to worked_hours not billed
    avg_hours_lost_df = selected_df.groupby(
        'Title')['hours_lost'].mean().reset_index()
    # round the average lost hours to 2 decimal places
    avg_hours_lost_df['hours_lost'] = round(avg_hours_lost_df['hours_lost'], 2)
    avg_hours_lost_df = avg_hours_lost_df.sort_values(
        by='hours_lost', ascending=False)
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=avg_hours_lost_df['Title'],
        y=avg_hours_lost_df['hours_lost'],
        name='Average Lost Hours',
        marker_color='lightsalmon',
        text=avg_hours_lost_df['hours_lost'],
        textposition='auto'))

    headline = 'The number of matters under current condition is ' + \
        str(num_of_matters)

    return html.Div(html.H1(headline)), html.Div(children=[
        html.Div(id='total-hours-by-level-section', children=[
            html.H2('The total hours by levels graph'),
            dcc.Graph(figure=fig)]),
        html.Br(),
        html.Div(id='average-hours-by-level-section', children=[
            html.H2('The average hours by levels graph'),
            dcc.Graph(figure=fig2)]),
        html.Br(),
        html.Div(id='total-amount-lost-by-level-section', children=[
            html.H2('The total amount lost due to exception rates by levels graph'),
            dcc.Graph(figure=fig3)]),
        html.Br(),
        html.Div(id='average-amount-lost-by-level-section', children=[
            html.H2('The average amount lost due to exception rates by levels graph'),
            dcc.Graph(figure=fig4)]),
        html.Br(),
        html.Div(id='total-hours-lost-by-level-section', children=[
            html.H2('The total lost due to not billed hours by levels graph'),
            dcc.Graph(figure=fig5)]),
        html.Br(),
        html.Div(id='average-hours-lost-by-level-section', children=[
            html.H2('The average lost due to not billed hours by levels graph'),
            dcc.Graph(figure=fig6)]),]
    ), None


def get_state_from_address(client_add: str) -> str:
    """
    Determines the state of a given address using the OpenAI API.

    Args:
        client_add (str): The address for which the state needs to be determined.

    Returns:
        str: The name of the state where the given address is located.
    """
    # Load the API key from the YAML file
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    client = OpenAI(
        api_key=config['openai_api_key'],
    )

    user_content = f'Which state is this address {client_add} in? Please just give me the state name as answer, in the form of json, word "state" as key and the actual state as value.'

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You helps me clean and understand client geographical information."},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
            max_tokens=64,
        )
        json_raw = response.choices[0].message.content
        json_object = json.loads(json_raw)
        return str(json_object["state"])

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# need to define a function to check the normality
# of the data before performing the hypothesis testing
def check_normality(data):
    test_stat_normality, p_value_normality = stats.shapiro(data)
    print("p value:%.4f" % p_value_normality)
    if p_value_normality < 0.05:
        print("Reject null hypothesis >> The data is not normally distributed")
    else:
        print("Accept null hypothesis >> The data is normally distributed")