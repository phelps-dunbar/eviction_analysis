import pandas as pd 
from elite_sql_call import run_query_elite

# Read in the data
df_40716 = pd.read_excel('Evictions Spreadsheet.xlsx', sheet_name = '40716 Monticello')
df_40418 = pd.read_excel('Evictions Spreadsheet.xlsx', sheet_name = '40418 Accolade')

# concat the data frames
odf = pd.concat([df_40716, df_40418]).rename(columns = {'mmatter': 'tmatter'})

# get the matter_ids from df
matter_ids = list(odf['tmatter'].unique())

# create a formatted string of matter_ids
# convert the list of matter_ids to a string format suitable for sql query
matter_ids_str = ','.join(id for id in matter_ids)

# from sql query get the other info about the matters
query = f'''SELECT *
        FROM timecard
        WHERE ((LEFT (tmatter, 5) = '40716'AND CAST(RIGHT(tmatter, 4) AS INT) <= 21)
        OR ((LEFT (tmatter, 5) = '40418' AND CAST(RIGHT(tmatter, 4) AS INT) <= 43)))
        '''
        
df = run_query_elite(query)
print(df.head())

# save the data frame to a csv
df.to_csv('evict_elite_info_raw.csv', index = False)

# change the workdate column into a datetime object
df['tworkdt'] = pd.to_datetime(df['tworkdt'])

# seperate 'write-off' and 'non-billable' ones
df_write_off = df[df['tstatus'] == 'BNP']
# df_non_billable = df[df['tstatus'] != 'NB']
# here there is no non-billable ones
#df_billable_but_not_billed = 
# looks like all not billed(billdt is null) are worked in the recent months
# so we are gonna ignore that for this project

# normal ones
df_normal = df[df['tstatus'] != 'BNP']

# for each matter_id, get the total hours worked and the total amount billed
df_normal_grouped = df_normal.groupby('tmatter').\
    agg({'tworkhrs': 'sum', 'tbilldol': 'sum'}).reset_index().\
    rename(columns = {'tworkhrs': 'total_hours_worked', 'tbilldol': 'total_amount_billed'})

# for each matter_id, get the number of timekeepers and time period from
# the first time worked to the last time worked
df_normal_grouped_2 = df_normal.groupby('tmatter').\
    agg({'tworkdt': ['min', 'max'], 'ttk': 'nunique'}).reset_index()

# create the time taken column from the first time worked to the last time worked
df_normal_grouped_2['time_taken'] = df_normal_grouped_2['tworkdt']['max'] - \
    df_normal_grouped_2['tworkdt']['min']

# drop the min and max columns
df_normal_grouped_2 = df_normal_grouped_2.drop(columns = ['tworkdt'])

# rename the columns and rest the index
df_normal_grouped_2.columns = ['tmatter', 'number_of_timekeepers', 'time_taken']
df_normal_grouped_2 = df_normal_grouped_2.reset_index(drop = True)
    
# for each matter_id, get the total write-off hours
df_write_off_grouped = df_write_off.groupby('tmatter').\
    agg({'tworkhrs': 'sum', 'tworkdol': 'sum'}).reset_index().\
    rename(columns = {'tworkhrs': 'total_write_off_hours', \
        'tworkdol': 'total_write_off_amount'})
    

# merge the data frames and the original data frame
df = odf.merge(df_normal_grouped, on = 'tmatter', how = 'left')
df = df.merge(df_normal_grouped_2, on = 'tmatter', how = 'left')
df = df.merge(df_write_off_grouped, on = 'tmatter', how = 'left')

print(df.head())

# save the data frame to a csv
df.to_csv('evict_elite_info.csv', index = False)

# check the end date for these matters
for id in df['tmatter'].unique():
    print(df[df['tmatter'] == id]['tworkdt'].max())