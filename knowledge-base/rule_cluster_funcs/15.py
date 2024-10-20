import sqlglot
from sqlglot import exp

def can_be_optimized_by_group_by_first(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by using GROUP BY first before JOIN
    
    :param sql_query: SQL query string
    :param table_schema: Table schema string (currently not used directly for checks)
    :param indexes: Indexes schema string  (currently not used directly for checks)
    :return: Boolean indicating potential for optimization
    """
    # Parse the SQL query using sqlglot
    try:
        parsed_query = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error parsing SQL query: {str(e)}")
        return False
    
    for node in parsed_query.find_all(exp.Select):
        if 'joins' in node.args and 'group' in node.args:
            return True

    return False