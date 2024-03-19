# this script is for preparing spread sheets
# so that we could talk about the outliers
# with the Dan, who is the Billing attorney

# import necessary libraries
import pandas as pd
import numpy as np
import os

df_tc = pd.read_csv('eviction_matter_tk_data.csv')
df_main = pd.read_csv('../ben_restyle/evict_elite_info.csv')

# join the two dataframes based on the matter_id
df = pd.merge(df_tc, df_main, left_on='matter_id',
              right_on='tmatter', how='left')

# drop the total_write_off_hours, total_write_off_amount columns
df.drop(['total_write_off_hours', 'total_write_off_amount',
        'tmatter'], axis=1, inplace=True)

# rename the columns for better understanding
df.rename(columns={"clname1": "client_name", "mdesc1": "matter_description", "pdesc": "practice_code",
                   "mopendt": "matter_open_date", "COUNTY": "county", "CATEGORY": "category"}, inplace=True)

df.to_csv('test_20240307.csv', index=False)

# define a function for the selecting a subset of the dataframe
# and save it to a xlsx file


def filter_and_save(df, county, client_name, category, filename):
    df_filtered = df[(df['county'] == county) & (
        df['client_name'] == client_name) & (df['category'] == category)]
    df_filtered.to_excel(filename, index=False)


filter_and_save(df, 'Dallas', 'Monticello Asset Management, Inc.',
                'Non-payment eviction at JP', 'outliers_Monti_dallas_NonPayJP.xlsx')
filter_and_save(df, 'Dallas', 'Monticello Asset Management, Inc.',
                'Non-payment eviction appeal', 'outliers_Monti_dallas_NonPayAppeal.xlsx')
filter_and_save(df, 'Denton', 'Accolade Property Management, Inc.',
                'Non-payment eviction appeal', 'outliers_Accol_denton_NonPayAppeal.xlsx')
filter_and_save(df, 'Tarrant', 'Accolade Property Management, Inc.',
                'Non-payment eviction appeal', 'outliers_Accol_tarrant_NonPayAppeal.xlsx')
filter_and_save(df, 'Travis', 'Accolade Property Management, Inc.',
                'Non-payment eviction appeal', 'outliers_Accol_travis_NonPayAppeal.xlsx')
