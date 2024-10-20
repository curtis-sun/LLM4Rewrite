import sqlglot
import sqlglot.expressions as exp

def can_be_optimized_by_and_or(sql_query, table_schema=None, indexes=None, dialect=None):
    """
    Check if a SQL query can be optimized by reorganizing AND and OR operators.
    """
    
    # Parse the SQL query to obtain an abstract syntax tree (AST)
    try:
        parsed = sqlglot.parse_one(sql_query, dialect=dialect)
    except Exception as e:
        print(f"Error while parsing SQL query: {e}")
        return False
    
    # Helper function to evaluate if an expression contains both AND and OR operators
    def evaluate_deep_and_or(expr):
        return len(list(expr.find_all(exp.And))) > 0 and len(list(expr.find_all(exp.Or))) > 0

    # Find all WHERE, HAVING and JOIN ON conditions
    conditions = [c.this for c in parsed.find_all(exp.Where, exp.Having)]
    joins = parsed.find_all(exp.Join)
    conditions.extend([join.args.get("on") for join in joins if "on" in join.args])

    # Check for constant conditions
    for condition in conditions:
        if evaluate_deep_and_or(condition):
            return True
    return False