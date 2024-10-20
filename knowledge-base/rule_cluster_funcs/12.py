import sqlglot
from sqlglot import exp

def can_be_optimized_by_inner_join_on(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by converting ON conditions of inner join to WHERE conditions
    
    :param sql_query: SQL query string
    :param table_schema: Table schema string (currently not used directly for checks)
    :param indexes: Indexes schema string  (currently not used directly for checks)
    :return: Boolean indicating potential for optimization
    """

    # Helper function to check whether a JOIN is INNER JOIN
    def is_inner_join(join):
        return 'kind' not in join.args and 'side' not in join.args or join.kind == 'INNER'
    
    # Parse the SQL query using sqlglot
    try:
        parsed_query = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error parsing SQL query: {str(e)}")
        return False
    
    for join in parsed_query.find_all(exp.Join):
        if is_inner_join(join) and 'on' in join.args:
            return True
    return False