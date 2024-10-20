import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import find_all_in_scope

def can_be_optimized_by_outer_join(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can potentially be optimized by converting OUTER JOINs to INNER JOINs
    """
    # Parse the SQL query using sqlglot
    try:
        parsed_query = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error parsing SQL query: {str(e)}")
        return False
    
    # Helper function to collect table names of the columns in the expression
    def column_table_names(expr):
        return {
            table
            for table in (column.table for column in find_all_in_scope(expr, exp.Column))
            if table
        }
    
    def get_table_name(expr):
        if isinstance(expr, exp.Table):
            return expr.this.this
        elif isinstance(expr, exp.Subquery):
            alias = expr.alias
            return alias if alias != "" else None
        return None

    # Helper function to check if a query has OUTER JOIN that can be optimized to INNER JOIN
    def evaluate_query(expr, tables):
        join_tables = []
        joins = []
        # Prepare the JOINs in the query
        if isinstance(expr, exp.Select):
            # Collect the tables involved in the WHERE clause
            if "where" in expr.args:
                where = expr.args.get("where")
                tables = tables.union(column_table_names(where))
            
            if 'from' in expr.args:
                join_tables.append(get_table_name(expr.args.get('from').this))
            joins = expr.args.get("joins", [])
        elif isinstance(expr, exp.Subquery):
            table = get_table_name(expr.this)
            join_tables.append(table)
            joins = expr.this.args.get("joins", [])
        
        for join in joins:
            right_table = get_table_name(join.this)
            join_tables.append(right_table)
        
        # From right to left to evaluate the JOINs
        on_condition_tables = set()
        for i in range(len(joins) - 1, -1, -1):
            join = joins[i]
            left_tables = join_tables[:i + 1]
            right_table = join_tables[i + 1]
            # Case when the left side is nullable
            if 'side' in join.args and join.args.get('side') == 'RIGHT' or \
                'side' not in join.args and 'kind' in join.args and join.args.get('kind') == 'OUTER':
                if any(t in tables for t in left_tables):
                    return True
            # Case when the right side is nullable
            if 'side' in join.args and join.args.get('side') == 'LEFT' or \
                'side' not in join.args and 'kind' in join.args and join.args.get('kind') == 'OUTER':
                if right_table in tables:
                    return True
            # Collect the tables involved in the ON condition
            if 'on' in join.args:
                on_condition_tables = on_condition_tables.union(column_table_names(join.args.get("on")))

            # Evaluate the JOIN inside, with the potential to push down ON conditions of the JOIN outside
            if isinstance(join.this, exp.Subquery) and evaluate_query(join.this, tables.union(on_condition_tables)):
                return True

        return False

    schema_dict = None
    if table_schema:
        schema_dict = {}
        try:
            for statement in sqlglot.parse(table_schema, dialect=dialect):
                if isinstance(statement, exp.Create):
                    table_name = statement.this.this.this.this
                    table_cols = {}
                    for col in statement.find_all(exp.ColumnDef):
                        col_name = col.this.this
                        col_type = col.kind
                        table_cols[col_name] = col_type
                    schema_dict[table_name] = table_cols
        except sqlglot.errors.ParseError:
            print("Error parsing schema.")
            schema_dict = None

    # Qualify the parsed query to resolve table references of columns
    parsed_query = qualify(parsed_query, schema=schema_dict)
    
    # Traverse the parsed query to find queries that can be optimized
    for node in parsed_query.find_all(exp.Select):
        if evaluate_query(node, set()):
            return True
    
    return False