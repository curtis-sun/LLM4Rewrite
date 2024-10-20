import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import find_all_in_scope
from sqlglot.optimizer.qualify import qualify

def can_be_optimized_by_filter_first_group_by_last(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Checks if the SQL query can be optimized by using filter before GROUP BY to reduce the size of the intermediate result set
    
    :param sql_query: SQL query string
    :param table_schema: Table schema string (currently not used directly for checks)
    :param indexes: Indexes schema string  (currently not used directly for checks)
    :return: Boolean indicating potential for optimization
    """

    # Helper function to collect table names of the columns in the expression
    def column_table_names(expr):
        return {
            table
            for table in (column.table for column in find_all_in_scope(expr, exp.Column))
            if table
        }
    
    # Helper function to extract the temporary table names involved in conditions
    def extract_condition_table_names(expr, table_names, subquery_aliases):
        if isinstance(expr, exp.Connector):
            extract_condition_table_names(expr.left, table_names, subquery_aliases)
            extract_condition_table_names(expr.right, table_names, subquery_aliases)
        else:
            condition_table_names = column_table_names(expr)
            if len(condition_table_names) == 1:
                table_name = list(condition_table_names)[0]
                if table_name in subquery_aliases:
                    table_names.add(table_name)

    # Parse the SQL query using sqlglot
    try:
        parsed_query = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error parsing SQL query: {str(e)}")
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
    
    parsed_query = qualify(parsed_query, schema=schema_dict)
    
    # Check if the query has Subqueries with GROUP BY
    subquery_aliases = []
    for node in parsed_query.find_all(exp.Subquery):
        if isinstance(node.this, exp.Select) and 'group' in node.this.args and node.args.get('alias', None):
            subquery_aliases.append(node.alias)

    if len(subquery_aliases) == 0:
        return False
    
    for node in parsed_query.find_all(exp.Select):
        # Check if the query has potential conditions to push down
        condition_table_names = set()
        if 'where' in node.args:
            extract_condition_table_names(node.args.get('where').this, condition_table_names, subquery_aliases)
        if 'joins' in node.args:
            for join in node.args.get('joins'):
                if 'on' in join.args:
                    extract_condition_table_names(join.args.get('on'), condition_table_names, subquery_aliases)

        for child in node.find_all(exp.Subquery):
            if isinstance(child.this, exp.Select) and child.args.get('alias', None) and child.alias in condition_table_names:
                return True
    return False