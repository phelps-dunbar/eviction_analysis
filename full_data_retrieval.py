# this script is for testing the new eviction analysis data
from elite_sql_call import run_query_elite

# this is the main function
query = '''
        SELECT m.mmatter as matter_id
        , c.clname1 as client_name
        , c.claddr1 as client_address1
        , c.claddr2 as client_address2
        , c.claddr3 as client_address3
        , c.claddr4 as client_address4
        , c.claddr5 as client_address5
        , c.claddr6 as client_address6
        , m.mdesc1 as matter_description
        , p.pdesc as practice_code
        , m.mopendt as matter_open_date
        , tc.ttk as timekeeper
        , d.head1 as department
        , loc.ldesc as location
        , tc.tworkhrs as worked_hours
        , tc.tworkrt as worked_rate
        , tc.tworkdol as worked_dollars
        , tc.tbillhrs as billed_hours
        , tc.tbillrt as billed_rate
        , tc.tbilldol as billed_dollars
        FROM matter AS m
        INNER JOIN praccode AS p
            ON m.mprac = p.pcode
        INNER JOIN client AS c
            ON m.mclient = c.clnum
        INNER JOIN timecard AS tc
            ON tc.tmatter = m.mmatter
        INNER JOIN deptlab AS d
            ON m.mdept = d.delcode
        INNER JOIN location AS loc
            ON m.mloc = loc.locode
        WHERE p.pdesc = 'LIT - Lease Evictions/Disputes'
        '''

df = run_query_elite(query)

print(df.head())

# drop the matter_id starting with 06089
# since they are probono matters
df = df[~df['matter_id'].str.startswith('06089')]
df.to_csv('eviction_data_full.csv', index=False)

# this query is for grouped data, so no specific timekeepers
# but only the total worked hours, worked amount, billed hours,
# billed amount for each matter
query2 = '''
        SELECT m.mmatter as matter_id
        , c.clname1 as client_name
        , m.mdesc1 as matter_description
        , c.claddr1 as client_address
        , p.pdesc as practice_code
        , m.mopendt as matter_open_date
        , d.head1 as department
        , loc.ldesc as location
        , sum(tc.tworkhrs) as total_worked_hours
        , sum(tc.tworkdol) as worked_dollars
        , sum(tc.tbillhrs) as billed_hours
        , sum(tc.tbilldol) as billed_dollars
        FROM matter AS m
        INNER JOIN praccode AS p
            ON m.mprac = p.pcode
        INNER JOIN client AS c
            ON m.mclient = c.clnum
        INNER JOIN timecard AS tc
            ON tc.tmatter = m.mmatter
        INNER JOIN deptlab AS d
            ON m.mdept = d.delcode
        INNER JOIN location AS loc
            ON m.mloc = loc.locode
        WHERE p.pdesc = 'LIT - Lease Evictions/Disputes'
        GROUP BY m.mmatter, c.clname1, m.mdesc1, p.pdesc, m.mopendt, d.head1, loc.ldesc, c.claddr1
        ORDER BY m.mmatter
        '''

# run the query
df2 = run_query_elite(query2)

# save the result
df2.to_csv('eviction_data_grouped.csv', index=False)

# looks like only 188 rows at all, let's try to see the full list of praccode
query_prac = '''
        SELECT *
        FROM praccode
        '''

df_prac = run_query_elite(query_prac)

df_prac.to_csv('praccode.csv', index=False)


# write another query to get the timekeeper information
# but this time use matter-timekeeper table instead of timecard

query_mt = '''
        SELECT m.mmatter as matter_id
        , c.clname1 as client_name
        , m.mdesc1 as matter_description
        , p.pdesc as practice_code
        , m.mopendt as matter_open_date
        , mt.mttk as timekeeper
        , d.head1 as department
        , loc.ldesc as location
        , mt.mthrwkdb as worked_hours
        , mt.mtdobidb as worked_dollars
        , mt.mtcrdb as credited_dollars
        FROM matter AS m
        INNER JOIN praccode AS p
            ON m.mprac = p.pcode
        INNER JOIN client AS c
            ON m.mclient = c.clnum
        INNER JOIN mattimhs AS mt
            ON mt.tmatter = m.mmatter
        INNER JOIN deptlab AS d
            ON m.mdept = d.delcode
        INNER JOIN location AS loc
            ON m.mloc = loc.locode
        WHERE p.pdesc = 'LIT - Lease Evictions/Disputes'
        '''
