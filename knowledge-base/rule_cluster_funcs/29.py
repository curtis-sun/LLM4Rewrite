import sqlglot
from sqlglot import exp

def can_be_optimized_by_subquery_to_exists(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can potentially be optimized by converting subqueries to EXISTS clauses
    
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

    # Helper function to evaluate if a subquery is present in specific conditions
    def evaluate_subquery(expr):
        if isinstance(expr, exp.In) and 'query' in expr.args or \
           isinstance(expr, exp.EQ) and isinstance(expr.right, exp.Any) and isinstance(expr.right.this, exp.Query):
            return True
        return False

    # Traverse the AST from the root
    for node in parsed_query.find_all(exp.In, exp.EQ):
        if evaluate_subquery(node):
            return True

    return False