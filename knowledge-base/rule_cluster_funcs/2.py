import sqlglot
from sqlglot import exp

def can_be_optimized_by_having(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by merging HAVING and WHERE clauses
    
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
        if 'having' in node.args and 'group' not in node.args:
            has_aggregate = False
            for expr in node.selects:
                if len(list(expr.find_all(exp.AggFunc))) > 0:
                    has_aggregate = True
                    break
            if not has_aggregate:
                return True
            
    return False