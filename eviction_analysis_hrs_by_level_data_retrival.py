# this script is for getting partner hours vs 
# non-partner hours for eviction analysis

import pandas as pd
from elite_sql_call import run_query_elite


# Read in the Original Data Frame
df_ori = pd.read_csv('evict_elite_info.csv')

# get the list of matter ids from df
matter_ids = list(df_ori['tmatter'].unique())

# define the sql query to get the data
query = f"""
        SELECT tc.tmatter AS matter_id
        , tc.ttk AS timekeeper_id
        , tk.tktitle AS tk_title
        , tr.tkrt01 AS standard_rate
        , tc.tbillrt AS billed_rate
        , tc.tworkhrs AS hours_worked
        , tc.tbillhrs AS hours_billed
        , tc.tworkdol AS amounts_worked
        , tc.tbilldol AS amounts_billed
        , tr.tkrt01 * tc.tbillhrs AS standard_rate_amount
        FROM timecard AS tc
        INNER JOIN matter AS m
            ON tc.tmatter = m.mmatter
        INNER JOIN timekeep AS tk
            ON tk.tkinit = tc.ttk
        INNER JOIN timerate AS tr
            ON tr.tkinit = tc.ttk
        WHERE mmatter IN ({', '.join("'" + str(id) + "'" for id in matter_ids)})
        """
        
# run the query
df = run_query_elite(query)

# group the data by each matter and the title level
# to calculate the sum of hours worked and billed,
# and also sum of amounts worked and billed
df_grouped = df.groupby(['matter_id', 'tk_title']).agg({'hours_worked': 'sum',
                                                        'hours_billed': 'sum',
                                                        'amounts_worked': 'sum',
                                                        'amounts_billed': 'sum',
                                                        'standard_rate_amount': 'sum'}).\
                                                            reset_index()
df_grouped = df_grouped.sort_values(by=['matter_id', 'tk_title'], ascending=True)

# I still need the category, client name from the original data frame
# merge it back
df_grouped = df_grouped.merge(df_ori[['tmatter', 'CATEGORY', 'clname1']], how='left', left_on='matter_id', right_on='tmatter')

# rename the columns for uniformity and drop the tmatter column
df_grouped.rename(columns={'CATEGORY': 'category',
                           'clname1': 'client_name'}, inplace=True)
df_grouped = df_grouped.drop(columns=['tmatter'])

# save the data frame
df_grouped.to_csv('evict_elite_hours_by_level.csv', index=False)