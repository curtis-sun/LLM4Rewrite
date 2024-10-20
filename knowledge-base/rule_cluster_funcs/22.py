import sqlglot
from sqlglot import exp

def can_be_optimized_by_window_order_over(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by windows sharing the same order or over clauses
    
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

    orders = set()
    overs = set()
    for window in parsed_query.find_all(exp.Window):
        # Check for repeated window over
        if 'over' in window.args:
            if window.args['over'] in overs:
                return True
            overs.add(window.args['over'])

        # Check for repeated window order
        if 'order' in window.args:
            if window.args['order'] in orders:
                return True
            orders.add(window.args['order'])
    return False
        