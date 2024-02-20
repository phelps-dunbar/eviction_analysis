import pymssql
import pandas as pd

def run_query_elite(query):
    """
    This function accepts a SQL query and executes that query against the elite database.
    query: A SQL query in form of a str
    """
    conn = pymssql.connect(
        'MS702DD08DEV001',
        'rouser',
        'readonly',
        "EliteReporting"
    ) # bad practice - update later - no conn details in github
    data = pd.read_sql(query, conn)

    assert len(data) != 0, "Resulting dataframe query is empty"
    
    return data

if __name__ == '__main__':

    query = """
        SELECT TOP 10 * FROM matter
        """

    print(run_query_elite(query))
    print("Shouldnt have failed ^")

    query = """
        SELECT TOP 0 * FROM matter
        """

    print("This should fail")
    print(run_query_elite(query))