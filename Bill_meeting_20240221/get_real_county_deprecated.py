# this script is for getting the real county of the property
# the deprecated version used chatgpt 4 model to find the real county
# of the property, but it is hard to get the desired ouput and
# since we only have small amount of data, we can use the
# manual method to find property asset from client's websites
# and then use the zip code API to get the real county of the property

# import the necessary libraries
import numpy as np
import pandas as pd
import requests
import yaml

# read the data
df = pd.read_excel('eviction_matter_county.xlsx', sheet_name="eviction_matter_county",
                   )

# change the "unknown" to np.nan
df['real_county'] = df['real_county'].replace('unknown', np.nan)

# add the state column, which is "TX" for all the matters
df['state'] = "TX"

# load in the api key
with open('api_key.yaml', 'r') as file:
    api_key = yaml.safe_load(file)['api_key']

# define the function to get the real county of the property


def get_real_county(city, state):

    assert len(
        state) == 2, "Invalid state, please use the abbreviation of the state"

    # the api url
    url = 'https://api.api-ninjas.com/v1/zipcode?city={}&state={}'.format(
        city, state)
    # get the response
    response = requests.get(url + city, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        return (response.text)
    else:
        return ("Error:", response.status_code, response.text)


# try the function
print(get_real_county('Dallas', 'TX'))
