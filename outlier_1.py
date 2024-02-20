# study the matter 20722-0007 since it's likely to be a outlier
from elite_sql_call import *

query = \
    '''
SELECT mth.mtmatter as matter_id
    , mth.mttk as timekeeper_id
    , mth.mtper as period
    , mth.mthrwkdw as hours_worked
    , mth.mtdowkdw as dollars_worked
FROM matter AS m
INNER JOIN mattimhs as mth
    ON m.mmatter = mth.mtmatter
WHERE mmatter = '20722-0007'
'''

df = run_query_elite(query)

# save the result
df.to_csv('outlier_1.csv', index=False)
