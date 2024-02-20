# this script is for comparing the standard rate of
# each matter to the actual billed amount (standard rate * hours worked)

# first impor
from elite_sql_call import run_query_elite

import pandas as pd



# only import the matter_ids in the eviction_data_full.csv
# this is the list of matter_ids that we want to compare
# to the standard rate

ev_df = pd.read_csv('eviction_data_full.csv')
tk = ev_df['timekeeper']
tk_list = []
for i in range(len(tk)):
    try:
        tk_list.append(str(int(tk[i])).zfill(5))
    except:
        print(i, tk[i])
        
# join the df with the eviction_data_full.csv
# on the matter_id
matter_list = ev_df['matter_id']


'''
query = f"""
WITH rates AS

(

SELECT b.tkinit AS tkrinit

,b.tkeffdate AS tkrdate1

,MIN(CASE WHEN e.tkeffdate IS NULL THEN '1/1/2026' ELSE e.tkeffdate END)-1 AS tkrdate2

,b.tkrt01

,b.tkrtcur

FROM timerate b

LEFT OUTER JOIN timerate e ON b.tkinit=e.tkinit AND e.tkeffdate > b.tkeffdate AND b.tkrtcur=e.tkrtcur

GROUP BY b.tkinit,b.tkeffdate,b.tkrt01,b.tkrtcur

)

SELECT

tksect AS 'PG'

,tkinit AS 'TK #'

,tkfirst+', '+tklast AS 'Timekeeper'

,tktitle AS 'Title'

,clnum AS 'Client #'

,clname1 AS 'Client'

, mmatter AS 'Matter #'

,tkstrate as tkstdrate

,SUM(tworkhrs) AS 'Worked Hrs'

,CAST(SUM(CASE WHEN rates.tkrt01 iS NULL THEN tworkhrs*dorates.tkrt01 ELSE tworkhrs*rates.tkrt01/cdrate END) AS DECIMAL(16,2)) AS 'R1 Fees'

,CAST(SUM(tworkdol/cdrate) AS DECIMAL(16,2)) AS 'Worked Fees'

,CAST(SUM(tbilldol/cdrate) AS DECIMAL(16,2)) AS 'Billed Fees'

FROM

timecard

INNER JOIN timekeep ON ttk=tkinit

INNER JOIN tsection ON tksect=tsection

INNER JOIN periodt ON tbiper=pe

INNER JOIN matter ON tmatter=mmatter

INNER JOIN client ON mclient=clnum

INNER JOIN currates ON mcurrency=curcode AND pebedt BETWEEN cddate1 AND cddate2 AND trtype='A'

LEFT OUTER JOIN rates ON rates.tkrinit=tkinit AND tworkdt BETWEEN rates.tkrdate1 AND rates.tkrdate2 AND mcurrency=rates.tkrtcur

LEFT OUTER JOIN rates dorates ON dorates.tkrinit=tkinit AND tworkdt BETWEEN dorates.tkrdate1 AND dorates.tkrdate2 AND dorates.tkrtcur='DO'

WHERE (tkinit IN {tuple(tk_list)}) OR (mmatter IN {tuple(matter_list)})

    AND tstatus NOT IN ('E','NBP')

GROUP BY tksect,tkinit,tklast,tkfirst, clnum, clname1, tktitle, tkstrate, mmatter

ORDER BY tksect, tklast
"""

# run the query
df = run_query_elite(query)

# print the results
print(df.head())

# export the results to excel
df.to_csv('elite_rates.csv', index=False)
'''


# read in the elite_rate
df = pd.read_csv('elite_rates.csv')

# compute the total worked hours, worked amount, billed hours, 
# billed amounts for each timekeeper and client_name
ev_df_grouped = ev_df.groupby(['matter_id', 'timekeeper']).\
    agg({'worked_hours': 'sum', 'worked_dollars': 'sum', 'billed_hours': 'sum', 'billed_dollars': 'sum'}).\
    reset_index()

# but I still want to keep the department and location information
# so I will merge the ev_df_grouped with the eviction_data_full.csv
# on the matter_id and timekeeper
ev_df_grouped = pd.merge(ev_df_grouped, ev_df[['matter_id', 'timekeeper', 'department', 'location']], how='left', on=['matter_id', 'timekeeper'])

ev_df_grouped['timekeeper'] = ev_df_grouped['timekeeper'].apply(lambda x: str(x).zfill(5))
df['TK #'] = df['TK #'].apply(lambda x: str(x).zfill(5))
    
# merge the two data frames
df_merged = pd.merge(ev_df_grouped, df, how='left', left_on=['matter_id', 'timekeeper'], right_on=['Matter #', 'TK #'])

# drop the duplicate columns
df_merged = df_merged.drop(['Matter #', 'TK #'], axis=1)

# calculate the actual rate so that we can compare it to the standard rate
df_merged['actual_rate'] = df_merged['billed_dollars'] / df_merged['billed_hours']

# calculate the standard rate * billed hours so that we can compare it to the billed amount
df_merged['std_rate_billed'] = df_merged['tkstdrate'] * df_merged['billed_hours']

# calculate the difference between the actual billed amount and the standard rate * billed hours
df_merged['profit_lost'] = df_merged['billed_dollars'] - df_merged['std_rate_billed']

# drop duplicated rows
df_merged = df_merged.drop_duplicates()

# drop the rows having NAs in Billed Fees column or Worked Fees column
df_merged = df_merged[~df_merged['Billed Fees'].isna()]
df_merged = df_merged[~df_merged['Worked Fees'].isna()]

# save the merged data frame to excel
df_merged.to_csv('elite_rates_merged.csv', index=False)

# for each matter, group by the title, calculate the 
# total worked hours, worked amount, billed hours, billed amount
# and the total standard rate * billed hours as budget_billed_amount
# and the total profit_lost as budget_profit_lost

df_merged_grouped = df_merged.groupby(['matter_id', 'Title']).\
    agg({'worked_hours': 'sum', 'worked_dollars': 'sum', \
        'billed_hours': 'sum', 'billed_dollars': 'sum', \
            'profit_lost': 'sum'}).reset_index()
    
# I still want the department and location information
# so I will merge the df_merged_grouped with the eviction_data_full.csv
# on the matter_id
df_merged_grouped = pd.merge(df_merged_grouped, 
                             ev_df[['matter_id', 'department', \
                                 'location']], how='left', 
                             on='matter_id')

# drop the duplicate rows
df_merged_grouped = df_merged_grouped.drop_duplicates()

# calculate the hours lost by using the difference between
# the total worked hours and the total billed hours
df_merged_grouped['hours_lost'] = df_merged_grouped['worked_hours'] - \
    df_merged_grouped['billed_hours']

# save the grouped data frame to csv
df_merged_grouped.to_csv('work_by_hours.csv', index=False)
    