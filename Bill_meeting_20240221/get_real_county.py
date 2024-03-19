# this script is for getting the real county of the property
# the deprecated version2 used zip code API to find the real county
# of the property, but it is hard to get the desired ouput and
# and I do get to the simple solution by downloading the data from
# "https://www.unitedstateszipcodes.org/zip-code-database/"
# so here we are

# import the necessary libraries
import numpy as np
import pandas as pd

# read the data
df = pd.read_excel('eviction_matter_county.xlsx',
                   sheet_name="eviction_matter_county",)

# read in the zip code data
df_zip = pd.read_excel("zip_code_database.xls")
print(df_zip.head())

# change the "unknown" to np.nan
df = df.replace('unknown', np.nan)

# add the state column, which is "TX" for all the matters
df['state'] = "TX"

# merge the data
df = df.merge(df_zip[['zip', 'county', 'irs_estimated_population']],
              how="left", left_on="property_zip_code", right_on="zip")
df = df.dropna()

# the county column values are all in format "CountyName County"
# but I just need the "CountyName" part
df['real_county'] = df['county'].apply(lambda x: x.split()[0])

df.to_csv("zip_test.csv", index=False)
