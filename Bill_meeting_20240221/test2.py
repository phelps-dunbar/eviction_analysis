from elite_sql_call import run_query_elite
from matter_tk_func import matter_tk_func
import numpy as np
import pandas as pd

query = '''
SELECT *
FROM timecard tc
INNER JOIN timekeep tk
    ON tc.ttk = tk.tkinit
WHERE LEFT(tmatter, 5) = '40716'
    OR LEFT(tmatter, 5) = '40418'
ORDER BY tmatter, tworkdt;
'''

df = run_query_elite(query)
print(df.head())
df.to_csv('eviction_tc_data_full.csv', index=False)

# get the timecard and timekeep data for the matter
matter_list = list(df['tmatter'].unique())

# Create an empty DataFrame
all_matters_df = pd.DataFrame()

for matter in matter_list:
    df = matter_tk_func(matter)
    print(df.head())
    all_matters_df = all_matters_df.append(df, ignore_index=True)

# generate the non_billed_hours column
all_matters_df['non_billed_hours'] = all_matters_df['total_work_hours'] - \
    all_matters_df['total_bill_hours']

# round the non_billed_hours column to 2 decimal places
all_matters_df['non_billed_hours'] = all_matters_df['non_billed_hours'].apply(
    lambda x: round(x, 2))

all_matters_df.to_csv('eviction_matter_tk_data.csv', index=False)
