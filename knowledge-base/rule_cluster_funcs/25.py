import sqlglot
import sqlglot.expressions as exp
from sqlglot.optimizer.scope import walk_in_scope
from collections import defaultdict

def can_be_optimized_by_constant_folding(sql_query, table_schema=None, indexes=None, dialect=None):

    COMPARISONS = (exp.LT, exp.LTE, exp.GTE, exp.GT, exp.EQ, exp.NEQ, exp.Is)
    EXTENDED_COMPARISONS = (exp.LT, exp.LTE, exp.GTE, exp.GT, exp.EQ, exp.NEQ, exp.Is, exp.Between, exp.In)

    def get_column_name(column: exp.Column) -> str:
        if column.args.get('table', None):
            return '.'.join([column.table, column.name])
        return column.name

    def find_parent_expr(expr):
        cur_expr = expr
        while cur_expr.parent:
            if isinstance(cur_expr.parent, exp.Connector):
                break
            cur_expr = cur_expr.parent
            if isinstance(cur_expr, exp.Where):
                break
        return cur_expr

    # Helper Function to collect columns from an expression except those in the conditions
    def collect_columns_except_conditions(expr, conditions):
        columns = {}
        for expr in walk_in_scope(expr, prune=lambda node: node in conditions):
            if isinstance(expr, exp.Column):
                columns[str(find_parent_expr(expr))] = get_column_name(expr)
        return columns

    # Helper function to check if an expression is constant
    def is_constant(expr):
        return len(list(expr.find_all(exp.Identifier))) == 0

    # Helper function to check if an expression is constant and reducible
    def is_reducible_constant(expr):
        return is_constant(expr) and not isinstance(expr, exp.CONSTANTS)

    # Helper function to search for constant conditions
    def evaluate_expression(expr):
        if isinstance(expr, exp.Connector):
            left_res, left_constant = evaluate_expression(expr.left)
            right_res, right_constant = evaluate_expression(expr.right)
            res = left_res + right_res
            left_columns = {str(find_parent_expr(c)): get_column_name(c) for c in expr.left.find_all(exp.Column)}
            right_columns = {str(find_parent_expr(c)): get_column_name(c) for c in expr.right.find_all(exp.Column)}
            if isinstance(expr, exp.And):
                # Check for common columns between the left and right expressions
                for k1, v1 in left_constant.items():
                    for k2, v2 in right_columns.items():
                        if v1 == v2 and k1 != k2:
                            res.append(f'{k1} ... {k2}')
                for k1, v1 in right_constant.items():
                    for k2, v2 in left_columns.items():
                        if v1 == v2 and k1 != k2:
                            res.append(f'{k2} ... {k1}')
            return res, dict(left_constant, **right_constant)
        elif isinstance(expr, (exp.Not, exp.Paren)):
            return evaluate_expression(expr.this)
        elif isinstance(expr, (exp.EQ, exp.Is)):
            if (isinstance(expr.left, exp.Column) and is_constant(expr.right)) or                (isinstance(expr.right, exp.Column) and is_constant(expr.left)):
                # Collect constant columns
                return [], {str(expr): get_column_name(expr.left)} if isinstance(expr.left, exp.Column) else {str(expr): get_column_name(expr.right)}
        return [], {}

    # Helper function to check if the expression is reducible
    def is_reducible(expr):
        if isinstance(expr, exp.Connector):
            left_exprs = is_reducible(expr.left)
            right_exprs = is_reducible(expr.right)
            if left_exprs and right_exprs:
                if left_exprs[0] == expr.left and right_exprs[0] == expr.right:
                    return [expr]
                return left_exprs + right_exprs
            elif left_exprs:
                return left_exprs
            elif right_exprs:
                return right_exprs
        elif isinstance(expr, (exp.Not, exp.Paren)):
            sub_exprs = is_reducible(expr.this)
            if sub_exprs:
                if sub_exprs[0] == expr.this:
                    return [expr]
                return sub_exprs
        else:
            # Check if the expression is constant
            flag = is_constant(expr)
            if flag:
                return [expr]
        return []
    
    # Helper function to check for column comparisons with reducible constant expressions
    def evaluate_column_reducible_constant_comparisons(expr):
        if isinstance(expr, COMPARISONS):
            if (isinstance(expr.left, exp.Column) and is_reducible_constant(expr.right)) or (isinstance(expr.right, exp.Column) and is_reducible_constant(expr.left)):
                return True
        elif isinstance(expr, exp.Between):
            if isinstance(expr.this, exp.Column) and (is_reducible_constant(expr.args.get('low')) or is_reducible_constant(expr.args.get('high'))):
                return True
        elif isinstance(expr, exp.In):
            if isinstance(expr.this, exp.Column) and any([is_reducible_constant(e) for e in expr.expressions]):
                return True
        return False

    # Helper function to track column comparisons with constants
    def track_column_constant_comparisons(expr, comparisons):
        if isinstance(expr, COMPARISONS):
            if isinstance(expr.left, exp.Column) and is_constant(expr.right):
                left_col_name = get_column_name(expr.left)
                if expr not in comparisons[left_col_name]:
                    comparisons[left_col_name].append(expr)
            elif isinstance(expr.right, exp.Column) and is_constant(expr.left):
                right_col_name = get_column_name(expr.right)
                if expr not in comparisons[right_col_name]:
                    comparisons[right_col_name].append(expr)
        elif isinstance(expr, exp.Between):
            if isinstance(expr.this, exp.Column) and is_constant(expr.args.get('low')) and is_constant(expr.args.get('high')):
                col_name = get_column_name(expr.this)
                if expr not in comparisons[col_name]:
                    comparisons[col_name].append(expr)
        elif isinstance(expr, exp.In):
            if isinstance(expr.this, exp.Column) and all([is_constant(e) for e in expr.expressions]) and ('query' not in expr.args or is_constant(expr.args.get('query'))):
                col_name = get_column_name(expr.this)
                if expr not in comparisons[col_name]:
                    comparisons[col_name].append(expr)
    
    try:
        parsed = sqlglot.parse_one(sql_query, dialect=dialect)
    except sqlglot.errors.ParseError:
        print("Error parsing SQL query.")
        return None
    
    # Find all WHERE, HAVING and JOIN ON conditions
    conditions = [c.this for c in parsed.find_all(exp.Where, exp.Having, bfs=False)]
    joins = parsed.find_all(exp.Join)
    conditions.extend([join.args.get("on") for join in joins if "on" in join.args])

    constant_foldings = set()
    # Check for constant conditions
    for condition in conditions:
        condition_exprs = is_reducible(condition)
        if condition_exprs:
            constant_foldings.update([f'```sql\n{expr}\n```' for expr in condition_exprs])

    # Dictionary to track column comparisons with constants
    column_constant_comparisons = defaultdict(list)
    for expr in parsed.find_all(EXTENDED_COMPARISONS, bfs=False):
        # Check for comparisons with reducible constant expressions
        if evaluate_column_reducible_constant_comparisons(expr):
            constant_foldings.add(f'```sql\n{expr}\n```')
        
        track_column_constant_comparisons(expr, column_constant_comparisons)

    # Check for columns compared with multiple constant expressions
    for constants in column_constant_comparisons.values():
        if len(constants) > 1:
            constants_str = ' ... '.join([str(c) for c in constants])
            constant_foldings.add(f'```sql\n{constants_str}\n```')
        
    # Evaluate whether the conditions contains constant columns
    constants = []
    for condition in conditions:
        res, constant = evaluate_expression(condition)
        for r in res:
            constant_foldings.add(f'```sql\n{r}\n```')
        constants.append(constant)

    for i in range(len(conditions)):
        conditions_except_i = conditions[:i] + conditions[i+1:]
        # Avoid recursively traverse the other conditions when collecting columns of the ith condition
        columns = collect_columns_except_conditions(conditions[i], conditions_except_i)
        for j in range(len(constants)):
            if i != j:
                # Check if a constant column is found in another condition
                for k1, v1 in constants[j].items():
                    for k2, v2 in columns.items():
                        if v1 == v2 and k1 != k2:
                            if i < j:
                                constant_foldings.add(f'```sql\n{k2} ... {k1}\n```')
                            else:
                                constant_foldings.add(f'```sql\n{k1} ... {k2}\n```')

    if len(constant_foldings) == 0:
        return None

    return 'Found expressions that may be optimized by constant folding:\n' + '\n'.join([f'{i + 1}. {expr}' for i, expr in enumerate(constant_foldings)])