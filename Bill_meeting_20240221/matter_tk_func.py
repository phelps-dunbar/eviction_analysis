# this script is for building a function for
# checking the working timekeeper for the matter and
# how many hours and how much money has been billed
# for the matter

from elite_sql_call import run_query_elite
import pandas as pd
import numpy as np
import os


def matter_tk_func(matter_id):
    '''
    This function takes in a matter_id and returns a dataframe
    for the timecard and timekeep data for the matter
    '''
    query = f'''
    SELECT tmatter AS matter_id,
    ttk as timekeeper_id,
    tkfirst + ' ' + tklast as timekeeper_name,
    tktitle as timekeeper_title,
    ROUND(AVG(tworkrt), 2) as weighted_avg_work_rate,
    ROUND(AVG(tbillrt), 2) as weighted_avg_bill_rate,
    ROUND(SUM(tworkhrs), 2) as total_work_hours,
    ROUND(SUM(tworkdol), 2) as total_work_dollars,
    ROUND(SUM(tbillhrs), 2) as total_bill_hours,
    ROUND(SUM(tbilldol), 2) as total_bill_dollars
    FROM timecard tc
    INNER JOIN timekeep tk
        ON tc.ttk = tk.tkinit
    WHERE tmatter = '{matter_id}'
    GROUP BY tmatter, ttk, tkfirst, tklast, tktitle
    ORDER BY tmatter;
    '''
    df = run_query_elite(query)
    return df


'''
    # run the query and get the data
    df = run_query_elite(query)

    # for each timekeeper, get the total hours and total dollars billed
    df['work_hours'] = df['work_hours'].astype(float)
    df['work_dollars'] = df['work_dollars'].astype(float)
    df['bill_hours'] = df['bill_hours'].astype(float)
    df['bill_dollars'] = df['bill_dollars'].astype(float)
    df['work_rate'] = df['work_rate'].astype(float)
    df['bill_rate'] = df['bill_rate'].astype(float)
    df['work_date'] = pd.to_datetime(df['work_date'])
    df['bill_date'] = pd.to_datetime(df['bill_date'])

    # create a new dataframe for the aggregated data
    # with the columns for the matter_id, timekeeper_id, timekeeper_name,
    # total_work_hours, total_work_dollars, total_bill_hours, total_bill_dollars,
    # weighted_avg_work_rate, weighted_avg_bill_rate
    df_new = pd.DataFrame(columns=['matter_id', 'timekeeper_id', 'timekeeper_name',
                                   'total_work_hours', 'total_work_dollars', 'total_bill_hours', 'total_bill_dollars',
                                   'weighted_avg_work_rate', 'weighted_avg_bill_rate'])

    # get the total hours and total dollars billed
    sum_work_hours = df.groupby('timekeeper_id')[
        'work_hours'].agg('sum')
    sum_work_dollars = df.groupby(
        'timekeeper_id')['work_dollars'].agg('sum')
    sum_bill_hours = df.groupby('timekeeper_id')[
        'bill_hours'].agg('sum')
    sum_bill_dollars = df.groupby(
        'timekeeper_id')['bill_dollars'].agg('sum')

    # calculate the weighted average work rate and bill rate
    df['weighted_avg_work_rate'] = df['total_work_dollars'] / df['total_work_hours']
    df['weighted_avg_bill_rate'] = df['total_bill_dollars'] / df['total_bill_hours']

    # drop the original columns and keep the aggregated columns
    # then drop the duplicates
    df = df.drop(columns=['work_hours', 'work_dollars',
                 'bill_hours', 'bill_dollars', 'work_rate', 'bill_rate'])
    df = df.drop_duplicates(subset=['timekeeper_id'])

    return df
'''
