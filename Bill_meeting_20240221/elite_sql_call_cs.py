import pymssql
import pandas as pd


def run_query_elite(query):
    """
    This function accepts a SQL query and executes that query against the elite database.
    query: A SQL query in form of a str
    """
    conn = pymssql.connect(
        'pdeuschangestreamsqlserver.database.windows.net',
        'changestream',
        'Change@stream',
        "changestream"
    )  # bad practice - update later - no conn details in github
    data = pd.read_sql(query, conn)

    assert len(data) != 0, "Resulting dataframe query is empty"

    return data


if __name__ == '__main__':

    query = """
        SELECT TOP 10 * FROM Matter
        """

    print(run_query_elite(query))
    print("Shouldnt have failed ^")

    query = """
        SELECT TOP 0 * FROM Matter
        """

    print("This should fail")
    print(run_query_elite(query))
