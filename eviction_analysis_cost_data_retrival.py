import pandas as pd
from elite_sql_call import run_query_elite

# Read in the Original Data Frame
df = pd.read_csv('test.csv')

# get the list of matter ids from df
matter_ids = tuple(df['matter_id'].unique())
print(matter_ids)

# Prepare data frames to hold data
df_cost = pd.DataFrame()

# create a sql query in which we want the all the cost related information
# for all the matters in the matter_ids list
# convert the list of matter_ids to a string format suitable for sql query

for matter in matter_ids:
    query = f'''SELECT cmatter AS matter_id,
                cdisbdt AS disbursement_date,
                cquant AS quantity,
                crate AS rate,
                camount AS amount,
                cbilldt AS date_billed,
                cbillamt AS amount_billed,
                ctk AS timekeeper,
                cstatus AS status_code,
                cledger AS ledger_code
                FROM COST AS c
                WHERE cmatter == '23198-0140'
                '''

    # run the query and get the data frame
    df_concat = run_query_elite(query)
    print(df_concat.head())
    df_cost = pd.concat([df_cost, df_concat], axis=0)

print(df_cost.head())

# in status_code column, rename 'B' to 'Billed' and 'BNP' to 'Written Off'
df_cost['status_code'] = df_cost['status_code'].\
    replace({'B': 'Billed', 'BNP': 'Written Off'})

# save the data frame to a csv
df_cost.to_csv('evict_elite_cost_info_raw.csv', index=False)
exit()

# group by matter_id and get the total amount billed and total amount
# for each matter_id
df_cost_grouped = df_cost.groupby('matter_id').\
    agg({'amount': 'sum', 'amount_billed': 'sum'}).reset_index().\
    rename(columns={'amount': 'total_cost_occurred',
           'amount_billed': 'total_cost_billed'})

# save the data frame to a csv
df_cost_grouped.to_csv('evict_elite_cost_info_grouped.csv', index=False)
