import copy
import sqlglot
import sqlglot.expressions as exp
import typing as t
from collections import defaultdict, deque
from sqlglot.optimizer.simplify import NONDETERMINISTIC
from sqlglot.optimizer.qualify import qualify

MIRROR_MAP = {exp.GT: exp.LT, exp.GTE: exp.LTE}
INTERCHANGE_LIST = (exp.Add, exp.Connector, exp.BitwiseAnd, exp.BitwiseOr, exp.BitwiseXor, exp.Overlaps, exp.EQ, exp.NullSafeEQ, exp.NullSafeNEQ, exp.Distance, exp.Mul, exp.NEQ, exp.Tuple, exp.In, exp.Group, exp.Partition, exp.Select, exp.Union, exp.Intersect)
MASKS = ['_', '?']

def get_column_name(column: exp.Column) -> str:
    if column.args.get('table', None):
        return '.'.join([column.table, column.name])
    return column.name

def is_equal(column: exp.Column, qualifier: str) -> bool:
    column_name = get_column_name(column)
    if '.' in column_name and '.' in qualifier:
        return column_name == qualifier
    return column_name.split('.')[-1] == qualifier.split('.')[-1]

def transform(node: exp.Expression, fun: t.Callable, *args: t.Any, copy: bool = True, **kwargs) -> exp.Expression:
        """
        Visits all tree nodes (excluding already transformed ones)
        and applies the given transformation function to each node.

        Args:
            fun: a function which takes a node as an argument and returns a
                new transformed node or the same node without modifications. If the function
                returns None, then the corresponding node will be removed from the syntax tree.
            copy: if set to True a new tree instance is constructed, otherwise the tree is
                modified in place.

        Returns:
            The transformed tree.
        """
        new_node = None

        for node in reversed(list((node.copy() if copy else node).dfs())):
            parent, arg_key, index = node.parent, node.arg_key, node.index
            new_node = fun(node, *args, **kwargs)

            if parent is not None and new_node is not node:
                parent.set(arg_key, new_node, index)

        assert new_node
        return new_node.assert_is(exp.Expression)

def equal_type(node1, node2):
    if type(node1) != type(node2):
        return False
    for k in node1.arg_types:
        if k in ['this', 'expression', 'expressions']:
            continue
        if k in node1.args and (k not in node2.args or node1.args.get(k) != node2.args.get(k)):
            return False
    return True

def compact_mask(l: t.List, mask: str) -> t.Tuple[int]:
    if mask not in l:
        return (-1, -1)
    left_i = l.index(mask)
    right_i = left_i + 1
    while right_i < len(l):
        if l[right_i] != mask:
            break
        right_i += 1
    return (left_i, right_i - 1)

def interchange(node: exp.Expression, reverse: bool = True) -> exp.Expression:
    if isinstance(node, INTERCHANGE_LIST):
        if 'expressions' in node.args:
            node.args['expressions'] = sorted(node.args['expressions'], key=lambda x: x.sql(), reverse=reverse)
        elif 'this' in node.args and 'expression' in node.args and (not node.parent or not equal_type(node.parent, node)):
            exprs = []

            nodes = deque([node])
            while len(nodes) > 0:
                n = nodes.popleft()

                if equal_type(n.this, node):
                    nodes.append(n.this)
                else:
                    exprs.append(n.this)

                if equal_type(n.args.get('expression'), node):
                    nodes.append(n.args.get('expression'))
                else:
                    exprs.append(n.args.get('expression'))
            
            exprs = sorted(exprs, key=lambda x: x.sql(), reverse=reverse)
            expr_sqls = [x.sql() for x in exprs]

            for mask in MASKS:
                (left_i, right_i) = compact_mask(expr_sqls, mask)
                if left_i != -1:
                    exprs = exprs[:left_i + 1] + exprs[right_i + 1:]
                    expr_sqls = expr_sqls[:left_i + 1] + expr_sqls[right_i + 1:]
                
            cur_node = exprs[0]
            for expr in exprs[1:]:
                nxt_node = node.copy()
                nxt_node.set('this', cur_node)
                nxt_node.set('expression', expr)
                cur_node = nxt_node
            node = cur_node
    return node

def mirror(node: exp.Expression) -> exp.Expression:
    for k,v in MIRROR_MAP.items():
        if isinstance(node, k):
            mirror_node = v()
            mirror_node.args = copy.deepcopy(node.args)
            mirror_node.args['this'] = node.args['expression']
            mirror_node.args['expression'] = node.args['this']
            return mirror_node
    return node

def preprocess(node):
    node.pop_comments()

    if isinstance(node, exp.Table):
        node.args.pop('db', None)

    elif isinstance(node, (exp.Literal, exp.Placeholder, exp.Parameter)):
        if node.parent and isinstance(node.parent, exp.Table) and node.parent.this == node:
            node = exp.Identifier(this='_')
        else:
            node = exp.Literal(this='?', is_string=False)

    else:
        node = mirror(node)
    return node

def has_no_star(node: exp.Expression) -> bool:
    for v in node.walk(prune= lambda x: isinstance(x, exp.Select)):
        if isinstance(v, exp.Star):
            return False
    return True

def is_masked(node: exp.Expression) -> bool:
    return node.sql() in MASKS

def is_identifiers_masked(node: exp.Expression) -> bool:
    flags = [v.this == '_' for v in node.find_all(exp.Identifier)]
    return all(flags) and len(list(node.find_all(NONDETERMINISTIC))) == 0 and has_no_star(node)

def is_constant(node: exp.Expression) -> bool:
    return len(list(node.find_all(tuple(list(NONDETERMINISTIC) + [exp.Identifier])))) == 0 and has_no_star(node)

def reduce_setop(node: exp.Expression) -> exp.Expression:
    if isinstance(node, (exp.Union, exp.Intersect, exp.Except)):
        if is_identifiers_masked(node.right):
            node = node.left
        elif is_identifiers_masked(node.left):
            node = node.right
    return node

def merge_join_subqueries(node: exp.Expression) -> exp.Expression:
    if isinstance(node, exp.Subquery) and isinstance(node.this, (exp.Table, exp.Subquery)) or\
       isinstance(node, exp.Table):
        node.args['this'] = merge_join_subqueries(node.this)

        if node.args.get('joins', None):
            joins = []
            for join in node.args.get('joins'):
                if not is_identifiers_masked(join):
                    join.set('this', merge_join_subqueries(join.this))
                    joins.append(join)

            if len(joins) > 0 and is_identifiers_masked(node.this):
                on_condition = joins[0].args.get('on', None)
                if not on_condition or is_identifiers_masked(on_condition):
                    node.set('this', joins[0].this)
                    joins = joins[1:]
            
            if len(joins) == 0:
                if isinstance(node, exp.Subquery):
                    node = node.this
                elif isinstance(node, exp.Table):
                    node.args.pop('joins', None)
            else:
                node.set('joins', joins)
        
    return node

def merge_tables(node: exp.Expression) -> exp.Expression:
    if isinstance(node, exp.Select):
        if node.args.get('from', None):
            node.args['from'].set('this', merge_join_subqueries(node.args.get('from').this))

        if node.args.get('joins', None):
            joins = []
            for join in node.args.get('joins'):
                if not is_identifiers_masked(join):
                    join.set('this', merge_join_subqueries(join.this))
                    joins.append(join)

            if len(joins) > 0 and is_identifiers_masked(node.args.get('from')):
                on_condition = joins[0].args.get('on', None)
                if not on_condition or is_identifiers_masked(on_condition):
                    node.args['from'].set('this', joins[0].this)
                    joins = joins[1:]
            
            if len(joins) > 0:
                node.set('joins', joins)
            else:
                node.args.pop('joins', None)
    
    else:
        node = reduce_setop(node)

    return node

def merge_columns(node: exp.Expression) -> exp.Expression:
    if isinstance(node, (exp.In, exp.Group, exp.Partition, exp.Select, exp.Tuple)):
        if 'expressions' in node.args:
            expressions = []
            for x in node.expressions:
                if not is_identifiers_masked(x):
                    expressions.append(x)
            if len(expressions) == 0:
                expressions = [exp.Column(this=exp.Identifier(this='_'))]
            node.args['expressions'] = expressions
    
    elif isinstance(node, exp.Order):
        if 'expressions' in node.args:
            last = 0
            for i, x in enumerate(node.expressions):
                if not is_identifiers_masked(x):
                    last = i
                    break
            node.args['expressions'] = node.expressions[:last+1]
    
    else:
        if isinstance(node, exp.Binary) and not isinstance(node, exp.Dot):
            if is_masked(node.right) and type(node.left) == type(node):
                return node.left
            elif is_masked(node.left) and type(node.right) == type(node):
                return node.right

        if isinstance(node, exp.Condition) and not isinstance(node, (exp.Column, exp.Boolean, exp.Null, exp.Literal)):
            if is_constant(node):
                if node.parent and isinstance(node.parent, exp.Table) and node.parent.this == node:
                    return exp.Identifier(this='_')
                return exp.Literal(this='?', is_string=False)
            
            if is_identifiers_masked(node):
                if node.parent and isinstance(node.parent, exp.Table) and node.parent.this == node:
                    return exp.Identifier(this='_')
                return exp.Column(this=exp.Identifier(this='_'))

    return node

def transform_column(node: exp.Expression, reserved_identifier: str = None, reserved_table: str = None) -> exp.Expression:
    if isinstance(node, exp.Column):
        if reserved_identifier and is_equal(node, reserved_identifier):
            node.args['this'].args['this'] = 'column'
        else:
            node.args['this'].args['this'] = '_'
        
        if node.args.get('table', None):
            if isinstance(node.this, exp.Star):
                if reserved_table and node.args.get('table').this == reserved_table:
                    node.args['table'].args['this'] = 'table'
                else:
                    node.args['table'].args['this'] = '_'
            else:
                node.args.pop('table', None)
    return node

def transformer(node: exp.Expression, reserved_identifier: str = None, reserved_table: str = None) -> exp.Expression:
    if isinstance(node, exp.Identifier):
        node.args.pop('quoted', None)
        if not node.parent or not isinstance(node.parent, (exp.Column, exp.Alias, exp.Table, exp.TableAlias)):
            node.args['this'] = '_'
    
    elif isinstance(node, exp.Column):
        if not node.parent or not isinstance(node.parent, exp.Alias):
            node = transform_column(node, reserved_identifier, reserved_table)

    elif isinstance(node, exp.Alias):
        transformed_column = None
        if isinstance(node.this, exp.Column):
            transformed_column = transform_column(node.this.copy(), reserved_identifier, reserved_table)
        reserved_col_name = reserved_identifier.split('.')[-1] if reserved_identifier else None
        if node.args.get('alias', None) and reserved_identifier and node.alias == reserved_col_name:
            if not isinstance(node.this, exp.Column):
                node.args['alias'].args['this'] = 'column'
            else:
                if transformed_column.name == '_' and node.this.name != reserved_col_name:
                    transformed_column.args['this'].args['this'] = 'column'
                
                if isinstance(node, exp.PivotAlias):
                    node.args['alias'].args['this'] = '_'
                else:
                    node.args.pop('alias', None)
        else:
            if isinstance(node, exp.PivotAlias):
                node.args['alias'].args['this'] = '_'
            else:
                node.args.pop('alias', None)
        if isinstance(node.this, exp.Column):
            node.set('this', transformed_column)

    elif isinstance(node, exp.TableAlias):
        if reserved_table and node.this.this == reserved_table:
            node.args['this'].args['this'] = 'table'
        else:
            node.args['this'].args['this'] = '_'

    elif isinstance(node, exp.Table):
        if node.args.get('this', None) and isinstance(node.this, exp.Identifier):
            if reserved_table and (node.this.this == reserved_table or node.args.get('alias', None) and node.alias == 'table'):
                node.args['this'].args['this'] = 'table'
            else:
                node.args['this'].args['this'] = '_'

            if node.args.get('alias', None) and node.name != '_':
                node.args.pop('alias', None)
    
    node = interchange(node)
    node = merge_columns(node)
    node = merge_tables(node)

    if not isinstance(node, exp.PivotAlias) and node.args.get('alias', None):
        if node.alias == '_':
            node.args.pop('alias', None)
    
    return node

def postprocess(node: exp.Expression) -> exp.Expression:
    if isinstance(node, exp.Select) and not node.args.get('distinct', None):
        if len(node.expressions) == 1 and is_masked(node.expressions[0]):
            node.args['expressions'] = [exp.Star()]
    return node

def format_sql(sql: str) -> str:
    return sql.replace('(', '( ').replace(')', ' )').replace(',', ' ,')

def reorder_connector(node: exp.Expression) -> exp.Expression:
    if isinstance(node, exp.And) and (not node.parent or not isinstance(node.parent, exp.And) or node.parent.right == node):
        exprs = []
        cur_node = node
        while isinstance(cur_node, exp.And):
            exprs.append(cur_node.right)
            cur_node = cur_node.left
        if isinstance(cur_node, exp.Or):
            exprs.append(cur_node.right)
            exprs = list(reversed(exprs))

            and_node = exprs[0]
            for expr in exprs[1:]:
                nxt_node = exp.And(this=and_node, expression=expr)
                and_node = nxt_node
            cur_node.set('expression', and_node)
            node = cur_node
    return node

def _gen_sql_template(parsed_tree: exp.Expression, col_name: str, table_name: str) -> str:
    transformed_tree = transform(parsed_tree, transformer, reserved_identifier=col_name, reserved_table=table_name)
    
    if 'with' in transformed_tree.args:
        for expr in transformed_tree.args.get('with').expressions:
            if 'alias' not in expr.args:
                expr.args['alias'] = exp.TableAlias(this=exp.Identifier(this='_'))
    post_tree = transform(transformed_tree, postprocess)

    post_sql = post_tree.sql()
    final_sql = format_sql(post_sql)
    return final_sql

def gen_sql_templates(sql: str, dialect: str = None) -> t.Dict[str, int]:
    expr_tree = sqlglot.parse_one(sql, dialect=dialect)
    expr_tree = transform(expr_tree, reorder_connector)

    ignore_exprs = []
    for node in expr_tree.find_all(exp.Select):
        if not node.args.get('distinct', None):
            for x in node.expressions:
                if isinstance(x, exp.Column) and not isinstance(node.this, exp.Star):
                    ignore_exprs.append(id(x))
                elif isinstance(x, exp.Alias) and isinstance(x.this, exp.Column):
                    ignore_exprs.append(id(x.this))
    
    col_counter = defaultdict(int)
    for node in expr_tree.find_all(exp.Column):
        if not isinstance(node.this, exp.Star) and id(node) not in ignore_exprs:
            col_counter[get_column_name(node)] += 1

    table_counter = defaultdict(int)
    for node in expr_tree.find_all(exp.Table):
        if node.name != '':
            table_counter[node.name] += 1

    covered_col_names = set()
    covered_table_names = set()
    for col_name in col_counter:
        if '.' in col_name:
            table_name = col_name.split('.')[0]
            if table_name in table_counter:
                covered_table_names.add(table_name)
            
            unqualified_name = col_name.split('.')[-1]
            if unqualified_name in col_counter:
                covered_col_names.add(unqualified_name)
                col_counter[col_name] += col_counter[unqualified_name]
            
    col_names = {k for k,v in col_counter.items() if v > 1 and k not in covered_col_names}
    table_names = {k for k,v in table_counter.items() if v > 1 and k not in covered_table_names}
    
    pre_tree = transform(expr_tree, preprocess)

    sql_scores = defaultdict(int)

    for col_name in col_names:
        table_name = None
        if '.' in col_name:
            table_name = col_name.split('.')[0]
        final_sql = _gen_sql_template(pre_tree, col_name, table_name)
        sql_scores[final_sql] += col_counter[col_name]

    for table_name in table_names:
        final_sql = _gen_sql_template(pre_tree, None, table_name)
        sql_scores[final_sql] += table_counter[table_name]

    return sql_scores