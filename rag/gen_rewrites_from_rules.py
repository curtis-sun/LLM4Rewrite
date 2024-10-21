import os
import asyncio
import json
import typing as t
import re
from llama_index.core.async_utils import run_async_tasks
import logging
from difflib import Differ 
from copy import deepcopy

from rag.prompts import *
from my_rewriter.rewrite import get_normal_rules
from my_rewriter.rewrite import match_all_rules, match_normal_rules

calcite_rules: t.Dict[str, str] = {}
with open('../explain_rule/calcite_rewrite_rules_structured.jsonl', 'r') as fin:
    for line in fin.readlines():
        rule = json.loads(line)
        rule_name = rule['name']
        sub_rules = rule['rewrite_rules_structured']
        sub_rules_str = '\n'.join([f'Case {i+1}:\n**Conditions**: {r["conditions"]}\n**Transformations**: {r["transformations"]}' for i, r in enumerate(sub_rules)]) if len(sub_rules) > 1 else f'**Conditions**: {sub_rules[0]["conditions"]}\n**Transformations**: {sub_rules[0]["transformations"]}'
        calcite_rules[rule_name] = sub_rules_str

rule_descriptions = {}
with open('../knowledge-base/rule_cluster_summaries_structured.jsonl', 'r') as fin:
    for line in fin:
        rule = json.loads(line)
        conditions = rule['conditions']
        transformations = rule['transformations']
        rule_descriptions[rule['index']] = f'**Conditions**: {conditions}\n**Transformations**: {transformations}'

rules_path = '../knowledge-base/rule_cluster_funcs'
for file in os.listdir(rules_path):
    filename = os.sep.join([rules_path, file])
    func_str = open(filename, 'r').read()
    exec(func_str, globals())

RULE_FUNCTIONS = [can_be_optimized_by_index_transformation, can_be_optimized_by_index_pushdown, can_be_optimized_by_having, can_be_optimized_by_subquery_to_join, can_be_optimized_by_index_like, can_be_optimized_by_index_block, can_be_optimized_by_and_or, can_be_optimized_by_multiple_indexes,can_be_optimized_by_outer_join, can_be_optimized_by_index_scan, can_be_optimized_by_set_op, can_be_optimized_by_right_join, can_be_optimized_by_inner_join_on, can_be_optimized_by_tight_index_scan, can_be_optimized_by_filter_first_group_by_last, can_be_optimized_by_group_by_first, can_be_optimized_by_limit, can_be_optimized_by_cte_filter_first_group_by_last, can_be_optimized_by_distinct, can_be_optimized_by_function, can_be_optimized_by_order_by_index, can_be_optimized_by_null, can_be_optimized_by_window_order_over, can_be_optimized_by_multiple_table_scan, can_be_optimized_by_non_deterministic_function, can_be_optimized_by_constant_folding, can_be_optimized_by_out_of_range, can_be_optimized_by_index_min_max, can_be_optimized_by_condition_pushdown, can_be_optimized_by_subquery_to_exists]

NL_RULES: t.List[str] = [r.__name__ for r in RULE_FUNCTIONS]
NORMAL_RULES: t.List[str] = get_normal_rules()

def match_nl_rules(sql: str, schema: str) -> t.List[t.Dict]:
    rules = []
    for i,func in enumerate(RULE_FUNCTIONS):
        try:
            res = func(sql, schema)
            if res:
                rule = {'name': func.__name__, 'description': rule_descriptions[i]}
                if isinstance(res, str):
                    rule['hint'] = res
                rules.append(rule)
        except Exception as e:
            logging.warn(e)
    return rules

def match_calcite_rules(sql: str, schema: str) -> t.List[t.Dict]:
    create_tables = [x for x in schema.split(';') if x.strip() != '']
    rule_objs = match_all_rules(sql, create_tables)
    
    rules = []
    for r in rule_objs:
        rule_name = str(r['name'])
        rule_type = str(r['type'])
        plan_before = str(r['plan_before'])
        plan_after = str(r['plan_after'])
        sub_rules = calcite_rules[rule_name]
        rules.append({'name': rule_name, 'type': rule_type, 'plan_before': plan_before, 'plan_after': plan_after, 'sub_rules': sub_rules})
    return rules

async def gen_rewrites_from_nl_rules(sql: str, matched_rules: t.List[t.Dict[str, str]], fun: t.Callable) -> t.List[t.Dict[str, str]]:
    if len(matched_rules) == 0:
        return []
    rules_str = '\n'.join([GEN_REWRITE_USER_RULE_HINT_PROMPT.format(rule_idx=i + 1, rule=rule['description'], rule_hint=rule['hint']) if 'hint' in rule else GEN_REWRITE_USER_RULE_PROMPT.format(rule_idx=i + 1, rule=rule['description']) for i,rule in enumerate(matched_rules)])
    gen_rewrite_user_message = GEN_REWRITE_USER_PROMPT.format(sql=sql, rules=rules_str)
    messages = [{'role': 'system', 'content': GEN_REWRITE_SYS_PROMPT}, {'role': 'user', 'content': gen_rewrite_user_message}]

    for _ in range(2):
        response = await fun(messages)
        
        delimiter = 'Step 2:'
        delimiter_idx = response.find(delimiter)
        if delimiter_idx != -1:
            step2 = response[delimiter_idx + len(delimiter):]

            segs = re.split(r'Query Rewrite (\d+):\s*"""', step2)
            rewrites = []
            for i in range(1, len(segs), 2):
                idx = segs[i]
                seg = segs[i + 1]
                end_idx = seg.rfind('"""')
                if end_idx != -1:
                    seg = seg[:end_idx]
                rewrites.append({'name': idx, 'rewrite': seg.strip()})
            if len(rewrites) > 0:
                return rewrites
    logging.warn(f"Failed to synthesize rewrites from NL rewrite rules: {response}")
    return []

async def gen_rewrite_from_calcite_sub_rule(rule_obj: t.Dict, sql: str, fun: t.Callable) -> t.Dict[str, str]:
    if rule_obj['type'] == 'explore':
        return rule_obj
    rule_name = rule_obj['name']
    sub_rules = rule_obj['sub_rules']
    plan_before = rule_obj['plan_before']
    plan_after = rule_obj['plan_after']
  
    differ = Differ()
    plan_changes = '\n'.join(differ.compare(plan_before.split('\n'), plan_after.split('\n')))

    gen_rewrite_user_message = GEN_CALCITE_REWRITE_USER_PROMPT.format(sql=sql, rule=sub_rules, plan_changes=plan_changes)
    messages = [{'role': 'system', 'content': GEN_CALCITE_REWRITE_SYS_RPOMPT}, {'role': 'user', 'content': gen_rewrite_user_message}]

    for _ in range(2):
        response = await fun(messages)
        
        delimiter = 'Step 4:'
        delimiter_idx = response.find(delimiter)
        if delimiter_idx != -1:
            rewrite = response[delimiter_idx + len(delimiter):].strip()
            res_obj = deepcopy(rule_obj)
            res_obj['rewrite'] = rewrite
            return res_obj
    logging.warn(f"Failed to synthesize rewrite from Calcite rule {rule_name}: {response}")
    res_obj = deepcopy(rule_obj)
    res_obj['rewrite'] = None
    return res_obj

async def gen_rewrites_from_calcite_rules(sql: str, calcite_rules: t.List[t.Dict[str, str]], fun: t.Callable) -> t.List[t.Dict[str, str]]:
    rewrites = []
    tasks = []
    for rule_obj in calcite_rules:
        tasks.append(gen_rewrite_from_calcite_sub_rule(rule_obj, sql, fun))

    task_results = await asyncio.gather(*tasks)
    rewrites = [r for r in task_results if 'rewrite' not in r or r['rewrite']]
    return rewrites

def gen_rewrites_from_rules(sql: str, schema: str, fun: t.Callable, verbose: bool = False) -> t.Tuple[t.Dict[str, t.List[t.Dict[str, str]]], t.Dict[str, t.List[str]]]:
    matched_nl_rules = match_nl_rules(sql, schema)
    nl_rule_names = [r['name'] for r in matched_nl_rules]
    if verbose:
        logging.info(f"Matched NL rewrite rules: {nl_rule_names}")
    matched_calcite_rules = []
    if schema:
        matched_calcite_rules = match_calcite_rules(sql, schema)
    normal_rule_names = [r['name'] for r in matched_calcite_rules if r['type'] == 'normal']
    explore_rule_names = [r['name'] for r in matched_calcite_rules if r['type'] == 'explore']
    if verbose:
        logging.info(f"Matched Calcite normalization rules: {normal_rule_names}")
        logging.info(f"Matched Calcite exploration rules: {explore_rule_names}")
    task_names = ['calcite', 'nl']
    tasks = []
    tasks.append(gen_rewrites_from_calcite_rules(sql, matched_calcite_rules, fun))
    tasks.append(gen_rewrites_from_nl_rules(sql, matched_nl_rules, fun))
    task_results = run_async_tasks(tasks)
    rewrites = {}
    for name, res in zip(task_names, task_results):
        rewrites[name] = res
    return rewrites, {'calcite_normal': normal_rule_names, 'calcite_explore': explore_rule_names, 'nl': nl_rule_names}

def get_one_hot(tot_rules: t.List[str], cur_rules: t.List[str]) -> t.List[float]:
    one_hot = [0] * len(tot_rules)
    for rule in cur_rules:
        one_hot[tot_rules.index(rule)] = 1
    return one_hot
    