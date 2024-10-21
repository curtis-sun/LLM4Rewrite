GEN_REWRITE_SYS_PROMPT  = '''You will be given a SQL query and some SQL query rewrite rules, each with the SQL conditions to apply the rule and the SQL transformations of the rule. Your task is to explain concisely and detailedly how the rewrite rules apply to the SQL query. Follow these steps:

Step 1: For each SQL query rewrite rule, use the provided rule's SQL conditions to identify the segments of the given SQL query that can be optimized by the rule. If there are no such segments, the rule does not match the SQL query. 

Step 2: For each SQL query rewrite rule that matches the SQL query, apply the provided rule's SQL transformations to the given SQL query. Explain this query rewrite process concisely and detailedly.

Output in the following format, where each query rewrite explanations are encapsulated with """:
Step 1: <step 1 reasoning>
Step 2:
Query Rewrite i: """<how the rewrite rule i applies to the SQL query, where i is the provided index of a matched rule>"""
...
'''

GEN_REWRITE_USER_PROMPT = '''
SQL Query:
```sql
{sql}
```

SQL Query Rewrite Rules:
{rules}'''

GEN_REWRITE_USER_RULE_PROMPT = '''Rule {rule_idx}:
"""
{rule}
"""'''

GEN_REWRITE_USER_RULE_HINT_PROMPT = '''Rule {rule_idx}:
"""
{rule}
**Hints**: {rule_hint}
"""'''

GEN_CALCITE_REWRITE_SYS_RPOMPT = '''You will be given a SQL query and a SQL query rewrite rule. You will also be provided with the logical plans changes after using the rule to rewrite the given SQL query. Your task is to explain how the query rewrite rule applies to the given SQL query. Follow these steps:

1. Use the provided logical plan changes after rewrite to identify the relational expression changes made by the query rewrite rule. 

2. Parse the logical plan changes into detailed changes of the given SQL query (e.g., involved SQL keywords, functions, literals, columns, tables).

3. If the SQL query rewrite rule contains multiple cases, you should use the parsed SQL query changes to specify which cases are matched during the query rewrite.

4. Use the matched cases to explain the SQL query changes. You should cite the detailed changes of the given SQL query to explain this query rewrite process concisely and detailedly.

Output in the following format:
Step 1: <step 1 reasoning>
Step 2: <step 2 reasoning>
Step 3: <step 3 reasoning>
Step 4: <step 4 reasoning>'''

GEN_CALCITE_REWRITE_USER_PROMPT = '''
SQL Query: ```sql\n{sql}\n```

Query Rewrite Rule: ```\n{rule}\n```

Logical Plan Changes After Rewrite: ```\n{plan_changes}\n```'''