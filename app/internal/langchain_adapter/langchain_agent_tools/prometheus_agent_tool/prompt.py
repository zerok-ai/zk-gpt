# flake8: noqa
QUERY_CHECKER = """
{query}
Double check the {dialect} query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.

SQL Query: """

PROMQL_QUERY_CHECKER = """
{query}
Double check the PromQL query above for common mistakes, including:
- Incorrect metric names or labels
- Using non-existent metric names
- Improper use of functions (e.g., rate(), sum(), avg())
- Incorrect time range in the query
- Missing or incorrect grouping in aggregation functions
- Proper handling of vector and scalar operations
- Proper use of alerting rules and conditions
- Correct usage of operators (e.g., ==, !=, =~, !~)

If there are any of the above mistakes, rewrite the PromQL query. If there are no mistakes, just reproduce the original query.

PromQL Query: """
