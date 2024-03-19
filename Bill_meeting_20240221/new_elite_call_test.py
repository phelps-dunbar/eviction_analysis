from elite_sql_call_cs import run_query_elite

query = """
    SELECT TOP 10 * FROM Matter
    """

print(run_query_elite(query))
