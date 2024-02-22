from elite_sql_call import run_query_elite
import numpy as np
import pandas as pd

# this scripts is for looking information in the evict elite information
query = '''
SELECT *
FROM matter
WHERE LEFT(mmatter,5) = '40716';
'''

df = run_query_elite(query)

df.to_csv('Monticello_Asset_Management_Inc.csv', index=False)
