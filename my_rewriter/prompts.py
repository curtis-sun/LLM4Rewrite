GEN_CASE_REWRITE_SYS_PROMPT = '''You will be given a SQL query and some query rewrite cases. Your task is to propose and explain some approaches to optimize the given SQL query through SQL query rewriting. Follow these steps:

Step 1: For each provided SQL query rewrite case, analyze whether the given SQL query can be rewritten in similar ways. From each query rewrite case, try to propose as many SQL query rewrite approaches as possible.

Step 2: Consider each proposed SQL query rewrite approach one-by-one. For a query rewrite approach, use it to rewrite the given SQL query. Explain this query rewrite process concisely and detailedly.

Output in the following format, where each query rewrite explanations are encapsulated with """:
Step 1: <step 1 reasoning>
Step 2:
Query Rewrite 1: """<explanation of proposed query rewrite approach 1>"""
...
Query Rewrite N: """<explanation of proposed query rewrite approach N>"""'''

GEN_CASE_REWRITE_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Cases:
{cases}'''

SELECT_CASE_RULE_SYS_PROMPT = '''You will be provided with a query rewrite case, and a list of SQL query rewrite rules. Your task is to identify the query rewrite rules that were applied in the query rewrite case. Follow these steps:

Step 1: For each provided SQL query rewrite rule, examine whether or not the query rewrite case applies the rule. Note that a query rewrite rule cannot be applied inversely.

Output in the following format:
Step 1: <step 1 reasoning>
then a python list of strings, where each string corresponds to the name of a query rewrite rule that was applied in the query rewrite case.'''

SELECT_CASE_RULE_USER_PROMPT = '''
Query Rewrite Case:
{case}

Query Rewrite Rules:
{rules}'''

CLUSTER_REWRITE_SYS_PROMPT = '''You will be given a SQL query and some strategies to rewrite the given SQL query. Your task is to cluster the provided query rewrite strategies.

Output a python list of objects encapsulated with ```python and ```, where each object is a python list of strategy indexes corresponding to a cluster.'''

CLUSTER_REWRITE_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Strategies:
{strategies}'''

SUMMARIZE_REWRITE_SYS_PROMPT = '''You will be given a SQL query and some strategies to rewrite the given SQL query. Your task is to summarize the provided query rewrite strategies into one paragraph.'''

SUMMARIZE_REWRITE_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Strategies:
{strategies}'''

SELECT_RULES_SYS_PROMPT =  '''You will be given a SQL query, some suggestions on how to rewrite the given SQL query, and some query rewrite rules to be selected. Your task is to select the rules that align with the provided suggestions. Follow these steps:\n\nStep 1: For each suggestion, you should evaluate all the query rewrite rules whether they can transform the given SQL query aligning with the suggestion. Note that one suggestion may require a combination of multiple rules.\n\nStep 2: Select the query rewrite rules that align with the provided query rewrite suggestions. But the given SQL query can just partially match the rule conditions, considering the combined effects of multiple rules.\n\nOutput in the following format:\nStep 1: <step 1 reasoning>\nStep 2: <step 2 reasoning>\n, then a python list of string encapsulated with ```python and ```, where each string corresponds to the name of a selected query rewrite rule.\n\nNotes:\n\n1. Ensure all the query rewrite rules are evaluated for every provided suggestion.\n2. It's acceptable to output an empty list if no rules align with the provided suggestions.'''

SELECT_RULES_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Suggestions:
{suggestions}

Query Rewrite Rules:
{rules}'''

ARRANGE_RULE_SETS_SYS_PROMPT = '''You will be given a SQL query, some suggestions on how to rewrite the given SQL query, some sets of query rewrite rules, and explanations of those rules. Each set of query rewrite rules involves the same relational operator, thus applying one query rewrite rule to the given SQL query may prevent another from being applied. Your task is to organize each rule set to best align with the provided query rewrite suggestions. Follow these steps:

Step 1: For each rule set, you should determine the sequence of the rules to best match the provided query rewrite suggestions, or you should prioritize more important rules over less important ones as suggested by the suggestions. Note that if some rules are not related to any suggestions, you should ignore them in your arrangement.

Output in the following format:
Step 1: <step 1 reasoning>
, then some python lists of string encapsulated with ```python and ```, where each string corresponds to the name of an arranged query rewrite rule, and the sequence of each list corresponds to the arranged order of each rule set. For instance,
<relational operator 1> Operator Rules: ```python
[
    <rule 1>,
    ...,
    <rule_n>
]
```
...'''

ARRANGE_RULE_SETS_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Suggestions:
{suggestions}

Query Rewrite Rule Sets:
{rule_sets}

Query Rewrite Rule Explanations:
{rules}'''

ARRANGE_RULES_SYS_PROMPT = '''You will be given a SQL query, some suggestions on how to rewrite the given SQL query, some query rewrite rules, and sequences for some rule subsets. Your task is to organize these query rewrite rules to optimize the given SQL query most effectively. Follow the provided rule subset sequences, and determine the overall sequence for all the rules.

Output in the following format:
<reasoning>
, then a python list of string encapsulated with ```python and ```, where each string corresponds to the name of an arranged query rewrite rule, and the sequence of the list corresponds to the arranged order of all the provided rules.'''

ARRANGE_RULES_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Suggestions:
{suggestions}

Query Rewrite Rules:
{rules}

Rule Subset Sequences:
{rule_sequences}'''

REARRANGE_RULES_SYS_PROMPT = '''You will be given a SQL query, some suggestions on how to rewrite the given SQL query, and some query rewrite rules. You will also be provided with an arranged sequence of those rules, the actually utilized rules, and the unutilized rules in that arrangement. Your task is to propose another rule arrangement to optimize the given SQL query more effectively. Follow these steps:

Step 1: For each unutilized rules in the provided arrangement, you should examine whether they match the provided query rewrite suggestions. If so, you should prioritize such unutilized potential rules over the utilized rules.

Step 2: Determine the overall sequence for all the rules, so that the new arrangement can better match the provided query rewrite suggestions.

Output in the following format:
Step 1: <step 1 reasoning>
Step 2: <step 2 reasoning>
, then a python list of string encapsulated with ```python and ```, where each string corresponds to the name of a re-arranged query rewrite rule, and the sequence of the list corresponds to the re-arranged order of all the provided rules.'''

REARRANGE_RULES_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Suggestions:
{suggestions}

Query Rewrite Rules:
{rules}

Arranged Rule Sequence: {arranged_rules}

Utilized Rules: {used_rules}

Unutilized Rules: {unused_rules}'''

SELECT_ARRANGE_RULES_SYS_PROMPT =  '''You will be provided with a SQL query and some query rewrite rules to be selected. Your task is to select the best list of the rules to improve the query's performance. Apply the selected rules step by step to transform the given SQL query into a new, optimized version that is the most efficient. \n\nOutput your reasoning steps, and a python list of strings encapsulated with ```python and ```,  where each string corresponds to the name of a selected query rewrite rule, and the sequence of the list corresponds to the arranged order of the selected rules.\n\nNote that you can output an empty list if the given query is already optimized and no query rewrite rules should be applied.'''

SELECT_ARRANGE_RULES_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

Query Rewrite Rules:
{rules}'''

RAG_SELECT_ARRANGE_RULES_SYS_PROMPT =  '''You will be provided with some query rewrite documents delimited by triple quotes, a SQL query, and some query rewrite rules to be selected. Using the provided documents as context, your task is to select the best list of the rules to improve the query's performance. Apply the selected rules step by step to transform the given SQL query into a new, optimized version that is the most efficient. \n\nOutput your reasoning steps, and a python list of strings encapsulated with ```python and ```,  where each string corresponds to the name of a selected query rewrite rule, and the sequence of the list corresponds to the arranged order of the selected rules.\n\nNote that you can output an empty list if the given query is already optimized and no query rewrite rules should be applied given the context.'''

RAG_SELECT_ARRANGE_RULES_USER_PROMPT = '''
Query Rewrite Documents as Context:
{documents}

SQL Query:
```sql
{sql}
```

Query Rewrite Rules:
{rules}''' 
