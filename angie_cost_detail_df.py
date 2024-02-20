# this script is for cost rate detail
import pandas as pd

from elite_sql_call import run_query_elite

# read in the eviction_data_full.csv to get the full matter list
full_df = pd.read_csv('eviction_data_grouped.csv')
matter_list = full_df['matter_id'].tolist()

# define the query from Angie
query = f"""
        select cost.ctk,tkfirst+' '+tklast as tkname,cmatter,clname1,mdesc1,cost.cindex,cdisbdt,ccode, cbillamt, cquant, crate, camount, cbilldt, ctk, tkfirst+' '+tklast, cstatus, cledger, (SELECT * FROM (SELECT(SELECT cddesc+'   ' AS [text()]

                            FROM costdesc WHERE costdesc.cindex=cost.cindex

                            ORDER BY cdline

                            FOR XML PATH('')

                    ) AS cddesc

                ) cddesc

        ) cddesc

        from cost,matter,timekeep,client

        where cmatter=mmatter

        and ctk = tkinit

        and mclient = clnum

        and cmatter in {tuple(matter_list)}

        order by cindex
        """
        
# run the query
df = run_query_elite(query)

# print the result
print(df)

# save the result to csv
df.to_csv('cost_rate_detail.csv',index=False)

# these costs are the inner cost occured in the firm, 
# not the cost billed to the client,
# mostly digital fees/ fedex fees, etc.

# for the meal to the customers, game ticket fees or
# any other things, we do not have them stored in the sql =
# database, they are stored in marketing montly reports,
# which is seperate excel files each for each practice group
# so......

# we do not need the full table, only need to group it by
# cstatus, B meaning Billed and BNP/BNC meaning write offs
# and then sum the camount as total inner cost
# and then group by cmatter to get the total inner cost for each matter
# and then merge the result with the eviction_data_full.csv

# read in the cost_rate_detail.csv
cost_df = pd.read_csv('cost_rate_detail.csv')


# for each matter, sum the 'BNP' and 'BNC' camount as write_off
# ans sum the 'B' camount as billed, and ignore the 'E' camount
# because it is not billed yet
# we only need the cmatter column, cstatus column and camount column
cost_df = cost_df[['cmatter','cstatus','camount']]
cost_df = cost_df.groupby(['cmatter','cstatus']).sum().reset_index()
for i in range(len(cost_df)):
    matter = cost_df.loc[i, 'cmatter']
    cost_df.loc[i, 'write_off'] = sum(cost_df[(cost_df['cmatter']==matter) \
        & (cost_df['cstatus'].isin(['BNP','BNC']))]['camount'])
    cost_df.loc[i, 'billed'] = sum(cost_df[(cost_df['cmatter']==matter) \
        & (cost_df['cstatus']=='B')]['camount'])
    
cost_df = cost_df[['cmatter','write_off','billed']].\
    rename(columns={'write_off':'write_off_inner_cost', 'billed':'billed_inner_cost'})
   
# merge the cost_df with the full_df
full_df = pd.merge(full_df, cost_df, how='left', \
    left_on='matter_id', right_on='cmatter')

# remove the cmatter column, since it's duplicated
full_df = full_df.drop('cmatter', axis=1)

# fill in the NAs in write_off and billed to 0s
full_df['write_off_inner_cost'] = full_df['write_off_inner_cost'].fillna(0)
full_df['billed_inner_cost'] = full_df['billed_inner_cost'].fillna(0)

# calculate the total billed cost
full_df['total_billed_cost'] = full_df['billed_inner_cost'] + full_df['billed_dollars']

# calculate the lawyer write off cost
full_df['write_off_lawyer_cost'] = full_df['worked_dollars'] - full_df['billed_dollars']

# calculate the total write off cost
full_df['total_write_off_cost'] = full_df['write_off_inner_cost'] + full_df['write_off_lawyer_cost']

# save the result to csv
full_df.to_csv('eviction_data_grouped.csv',index=False)