import sqlglot
from sqlglot import exp

def can_be_optimized_by_index_transformation(sql_query: str, schema: str = None, indexes: str = None, dialect: str = None) -> bool:
    """
    Check if the given SQL query can be optimized by existing indexes or primary key using some transformations.
    """

    COMPARISONS = (exp.LT, exp.LTE, exp.GTE, exp.GT, exp.EQ, exp.NEQ, exp.Is)

    # Helper function to check if an expression is constant
    def is_constant(expr):
        return len(list(expr.find_all(exp.Identifier))) == 0
    
    # Helper function to extract the columns involved in conditions
    def extract_condition_columns(expr, columns, potential_columns):
        if isinstance(expr, exp.Connector):
            extract_condition_columns(expr.left, columns, potential_columns)
            extract_condition_columns(expr.right, columns, potential_columns)
        elif isinstance(expr, (exp.Not, exp.Paren)):
            extract_condition_columns(expr.this, columns, potential_columns)
        else:
            if isinstance(expr, COMPARISONS):
                if isinstance(expr.left, exp.Column) and is_constant(expr.right):
                    columns.add(expr.left.this)
                    return
                elif isinstance(expr.right, exp.Column) and is_constant(expr.left):
                    columns.add(expr.right.this)
                    return
            elif isinstance(expr, exp.Between):
                if isinstance(expr.this, exp.Column) and is_constant(expr.args.get('low')) and is_constant(expr.args.get('high')):
                    columns.add(expr.this.this)
                    return
            elif isinstance(expr, exp.In):
                if isinstance(expr.this, exp.Column) and all([is_constant(e) for e in expr.expressions]) and ('query' not in expr.args or is_constant(expr.args.get('query'))):
                    columns.add(expr.this.this)
                    return
            condition_columns = set([c.this for c in expr.find_all(exp.Column)])
            if len(condition_columns) == 1:
                potential_columns.add(list(condition_columns)[0])

    # Helper function to parse the indexes from table schema and indexes
    def parse_schema_indexes(schema: str, indexes: str) -> dict:
        """
        Parse the table schema and indexes to get the organized structure 
        and the defined indexes on the table.
        """
        parsed_indexes = {}
        if schema:
            for statement in sqlglot.parse(schema, dialect=dialect):
                if isinstance(statement, exp.Create):
                    pk_name = statement.this.sql()
                    flag = False
                    for expr in statement.this.args.get('expressions', []):
                        if isinstance(expr, exp.ColumnDef):
                            for constraint in expr.args.get('constraints', []):
                                if constraint.args.get('kind', None) and isinstance(constraint.kind, exp.PrimaryKeyColumnConstraint):
                                    parsed_indexes[pk_name] = [expr.this]
                                    flag = True
                                    break
                            if flag:
                                break
                    if not flag:
                        for constraint in statement.find_all(exp.PrimaryKey):
                            parsed_indexes[pk_name] = list(constraint.expressions)
                            break
        if indexes:
            for idx_stmt in indexes.split(";"):
                idx_stmt = idx_stmt.strip()
                if idx_stmt:
                    statement = sqlglot.parse_one(idx_stmt, dialect=dialect)
                    if isinstance(statement, exp.Create):
                        index_name = statement.this.sql()
                        columns = [col.this for col in statement.find_all(exp.Column)]
                        if len(columns) > 0:
                            parsed_indexes[index_name] = columns
        return parsed_indexes

    # Parse the SQL query to extract the AST
    try:
        parsed = sqlglot.parse_one(sql_query, dialect=dialect)
    except sqlglot.errors.ParseError:
        print("Error parsing SQL query.")
        return False

    # Find all WHERE, HAVING and JOIN ON conditions
    conditions = [c.this for c in parsed.find_all(exp.Where, exp.Having)]
    joins = parsed.find_all(exp.Join)
    conditions.extend([join.args.get("on") for join in joins if "on" in join.args])

    # Extract columns involved in conditions
    comparison_columns = set()
    potential_columns = set()
    for condition in conditions:
        extract_condition_columns(condition, comparison_columns, potential_columns)

    # Parse the table schema and existing indexes
    parsed_indexes = parse_schema_indexes(schema, indexes)

    # Check if extracted columns can benefit from any index
    for index_columns in parsed_indexes.values():
        i = 0
        while i < len(index_columns):
            if index_columns[i] in comparison_columns:
                i += 1
            else:
                break
        if i < len(index_columns) and index_columns[i] in potential_columns:
            return True  # Found an index that could potentially optimize the query
    return False