import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import find_all_in_scope

def can_be_optimized_by_cte_filter_first_group_by_last(sql_query, table_schema=None, indexes=None, dialect=None):
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
    
    # Helper function to extract the derived table names involved in conditions
    def extract_condition_table_names(expr, table_names, cte_aliases):
        if isinstance(expr, exp.Connector):
            extract_condition_table_names(expr.left, table_names, cte_aliases)
            extract_condition_table_names(expr.right, table_names, cte_aliases)
        else:
            condition_table_names = column_table_names(expr)
            if len(condition_table_names) == 1:
                table_name = list(condition_table_names)[0]
                if table_name in cte_aliases:
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
    
    # Check if the query has CTEs with GROUP BY
    cte_aliases = []
    if 'with' in parsed_query.args:
        for expr in parsed_query.args.get('with').expressions:
            if len(list(expr.find_all(exp.Group))) > 0:
                cte_aliases.append(expr.alias)

    if len(cte_aliases) == 0:
        return False
    
    for node in parsed_query.find_all(exp.Select):
        # Check if the query has potential conditions to push down
        condition_table_names = set()
        if 'where' in node.args:
            extract_condition_table_names(node.args.get('where').this, condition_table_names, cte_aliases)
        if 'joins' in node.args:
            for join in node.args.get('joins'):
                if 'on' in join.args:
                    extract_condition_table_names(join.args.get('on'), condition_table_names, cte_aliases)

        for child in node.walk(prune=lambda x: isinstance(x, exp.CTE)):
            if isinstance(child, exp.Table):
                if child.name in condition_table_names:
                    return True
    return False