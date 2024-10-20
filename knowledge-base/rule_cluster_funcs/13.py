import sqlglot
from sqlglot import exp

def can_be_optimized_by_tight_index_scan(sql_query: str, schema: str = None, indexes: str = None, dialect: str = None) -> bool:
    """
    Check if the given SQL query can be optimized by Tight Index Scan.
    """

    # Helper function to check if an expression is constant
    def is_constant(expr):
        return len(list(expr.find_all(exp.Identifier))) == 0
    
    # Helper function to extract the columns equal to constants
    def extract_equal_columns(expr, columns):
        if isinstance(expr, exp.Connector):
            extract_equal_columns(expr.left, columns)
            extract_equal_columns(expr.right, columns)
        elif isinstance(expr, (exp.Not, exp.Paren)):
            extract_equal_columns(expr.this, columns)
        elif isinstance(expr, (exp.EQ, exp.Is)):
            if isinstance(expr.left, exp.Column) and is_constant(expr.right):
                columns.add(expr.left.this)
            elif isinstance(expr.right, exp.Column) and is_constant(expr.left):
                columns.add(expr.right.this)

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

    # Find all WHERE and JOIN ON conditions
    conditions = [c.this for c in parsed.find_all(exp.Where)]
    joins = parsed.find_all(exp.Join)
    conditions.extend([join.args.get("on") for join in joins if "on" in join.args])

    # Extract columns equal to constants
    equal_columns = set()
    for condition in conditions:
        extract_equal_columns(condition, equal_columns)

    # Parse the table schema and existing indexes
    parsed_indexes = parse_schema_indexes(schema, indexes)

    # Check if GROUP BY can benefit from any index with the help of equality conditions on the index columns
    for node in parsed.find_all(exp.Group):
        # Extract the columns in the GROUP BY clause
        group_columns = set()
        for expr in node.expressions:
            if not isinstance(expr, exp.Column):
                return False
            group_columns.add(expr.this)

        # Check if the GROUP BY columns are prefix of any index columns with the help of equality conditions
        for index_columns in parsed_indexes.values():
            if not all(col in group_columns for col in index_columns[:len(group_columns)]):
                i = 0
                for col in index_columns:
                    if col in group_columns:
                        i += 1
                        if i == len(group_columns):
                            return True
                    elif col not in equal_columns:
                        break
                if i == len(group_columns):
                    return True
    
    return False