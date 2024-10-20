import sqlglot
from sqlglot import exp

def can_be_optimized_by_multiple_table_scan(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by merging multiple table scans into a single scan
    
    :param sql_query: SQL query string
    :param table_schema: Table schema string (currently not used directly for checks)
    :param indexes: Indexes schema string  (currently not used directly for checks)
    :return: Boolean indicating potential for optimization
    """

    # Helper function to get the table name from the expression
    def get_table_name(expr):
        if isinstance(expr, exp.Table):
            return expr.this.this
        elif isinstance(expr, exp.Subquery):
            alias = expr.alias
            return alias if alias != "" else None
        return None

    # Parse the SQL query using sqlglot
    try:
        parsed_query = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error parsing SQL query: {str(e)}")
        return False

    # Traverse the tables of every FROM clause and JOIN clause to check if any table is repeated
    table_names = set()
    for node in parsed_query.find_all(exp.Select):
        if 'from' in node.args:
            table = get_table_name(node.args.get('from').this)
            if table:
                if table in table_names:
                    return True
                table_names.add(table)
        
        if 'joins' in node.args:
            for join in node.args.get('joins'):
                join_table = get_table_name(join.this)
                if join_table:
                    if join_table in table_names:
                        return True
                    table_names.add(join_table)

    return False