# this script is for find the real county of the
# matters using chatgpt 4 model
# the current county aligned with the matters
# are using the county in which the client is located
# instead of the real county of the property

from call_gpt import chat_completion
import numpy as np
import pandas as pd
from elite_sql_call import run_query_elite

'''
# query =
SELECT mmatter as matter_id,
mdesc1 as matter_description1,
mdesc2 as matter_description2,
mdesc3 as matter_description3
FROM matter
WHERE LEFT(mmatter, 5) = '40716'
    OR LEFT(mmatter, 5) = '40418'
ORDER BY mmatter;

df = run_query_elite(query)
df.to_csv('eviction_matter_description.csv', index=False)
print(df.head())
exit()
'''
# the upper code is only needed in the first run

# read the data
df = pd.read_csv('eviction_matter_description.csv')

# join the matter descriptions into one string
df['matter_desc'] = df['matter_description1'] + ' ' + \
    df['matter_description2'] + ' ' + df['matter_description3']

# add the df column for the real county of the property
df['real_county'] = np.nan

# using the chatgpt 4 model to find the real county of the matters
# using the matter descriptions
for i in range(len(df)):
    matter_desc = df['matter_desc'][i]
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant in determining the county of these addresses in Texas. If you can decide the county of the property, please provide the county name. If you are not sure, please return unknown.'},
        {'role': 'user', 'content': f'based on these information {matter_desc}, what is the real county of the property?'}
    ]
    response = chat_completion(messages)
    print(response)
    df['real_county'][i] = response

print(df.head())
df.to_csv('eviction_matter_county.csv', index=False)
