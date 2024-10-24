from typing import Any, Dict, List, Optional, Sequence, Union, cast, Tuple
import typing as t
import re
import logging
import time
import openai
from collections import defaultdict
import asyncio

from llama_index.core.llms import LLM
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core import Settings
from llama_index.core.schema import (
    BaseNode,
    TextNode,
    NodeWithScore
)
from llama_index.llms.openai import OpenAI

from my_rewriter.case_rules import case_rules, add_case_rules
from rag.gen_rewrites_from_rules import calcite_rules

SELECT_CASE_RULE_MODEL = OpenAI(
    model="gpt-4-0125-preview"
)

def chat(messages: List[Dict]) -> str:
    chat_messages = [ChatMessage(**m) for m in messages]
    start = time.time()
    response = Settings.llm.chat(chat_messages)
    logging.debug({'messages': messages, 'response': response.message.content, 'time': time.time() - start})
    return response.message.content

async def achat(messages: List[Dict], model: LLM = None) -> str:
    if model is None:
        model = Settings.llm
    chat_messages = [ChatMessage(**m) for m in messages]
    start = time.time()
    try:
        response = await model.achat(chat_messages)
    except (ConnectionResetError, openai.APIConnectionError):
        time.sleep(5)
        response = await model.achat(chat_messages)
    logging.debug({'messages': messages, 'response': response.message.content, 'time': time.time() - start})
    return response.message.content

def get_rule_sets(rule_names: t.List[str]) -> t.Dict[str, t.List[str]]:
    rule_groups_dict  = {}
    for ops in CALCITE_OPERATOR_GROUPS:
        group = []
        for r in rule_names:
            for op in ops:
                if op in r:
                    group.append(r)
                    break
        if len(group) > 1:
            rule_groups_dict[op] = group
    return rule_groups_dict

RULE_DIVISIONS = [
    ['AGGREGATE_ANY_PULL_UP_CONSTANTS',
    'AGGREGATE_CASE_TO_FILTER',
    'AGGREGATE_EXPAND_DISTINCT_AGGREGATES',
    'AGGREGATE_JOIN_JOIN_REMOVE',
    'AGGREGATE_JOIN_REMOVE',
    'AGGREGATE_MERGE',
    'AGGREGATE_PROJECT_MERGE',
    'AGGREGATE_REMOVE',
    'AGGREGATE_VALUES',
    'AGGREGATE_EXPAND_DISTINCT_AGGREGATES_TO_JOIN',
    'AGGREGATE_FILTER_TRANSPOSE',
    'AGGREGATE_JOIN_TRANSPOSE_EXTENDED',
    'AGGREGATE_REDUCE_FUNCTIONS',
    'AGGREGATE_UNION_TRANSPOSE',
    'AGGREGATE_UNION_AGGREGATE_FIRST',
    'AGGREGATE_UNION_AGGREGATE_SECOND',
    'WINDOW_REDUCE_EXPRESSIONS'],
    ['FILTER_AGGREGATE_TRANSPOSE',
    'FILTER_CORRELATE',
    'FILTER_EXPAND_IS_NOT_DISTINCT_FROM',
    'FILTER_INTO_JOIN',
    'FILTER_MERGE',
    'FILTER_PROJECT_TRANSPOSE',
    'FILTER_REDUCE_EXPRESSIONS',
    'FILTER_SET_OP_TRANSPOSE',
    'FILTER_SUB_QUERY_TO_CORRELATE',
    'FILTER_TABLE_FUNCTION_TRANSPOSE',
    'FILTER_VALUES_MERGE',
    'SORT_REMOVE',
    'SORT_REMOVE_CONSTANT_KEYS',
    'SORT_PROJECT_TRANSPOSE',
    'SORT_JOIN_TRANSPOSE',
    'SORT_UNION_TRANSPOSE',
    'SORT_UNION_TRANSPOSE_MATCH_NULL_FETCH'],
    ['JOIN_CONDITION_PUSH',
    'JOIN_PUSH_TRANSITIVE_PREDICATES',
    'JOIN_REDUCE_EXPRESSIONS',
    'JOIN_SUB_QUERY_TO_CORRELATE',
    'JOIN_ADD_REDUNDANT_SEMI_JOIN',
    'JOIN_DERIVE_IS_NOT_NULL_FILTER_RULE',
    'JOIN_EXTRACT_FILTER',
    'JOIN_PROJECT_BOTH_TRANSPOSE_INCLUDE_OUTER',
    'JOIN_PROJECT_LEFT_TRANSPOSE_INCLUDE_OUTER',
    'JOIN_PROJECT_RIGHT_TRANSPOSE_INCLUDE_OUTER',
    'JOIN_PUSH_EXPRESSIONS',
    'JOIN_TO_CORRELATE',
    'JOIN_LEFT_UNION_TRANSPOSE',
    'JOIN_RIGHT_UNION_TRANSPOSE',
    'SEMI_JOIN_FILTER_TRANSPOSE',
    'SEMI_JOIN_PROJECT_TRANSPOSE',
    'SEMI_JOIN_JOIN_TRANSPOSE'],
    ['PROJECT_AGGREGATE_MERGE',
    'PROJECT_FILTER_VALUES_MERGE',
    'PROJECT_JOIN_JOIN_REMOVE',
    'PROJECT_JOIN_REMOVE',
    'PROJECT_MERGE',
    'PROJECT_REDUCE_EXPRESSIONS',
    'PROJECT_REMOVE',
    'PROJECT_SUB_QUERY_TO_CORRELATE',
    'PROJECT_VALUES_MERGE',
    'PROJECT_CORRELATE_TRANSPOSE',
    'PROJECT_FILTER_TRANSPOSE',
    'PROJECT_TO_LOGICAL_PROJECT_AND_WINDOW',
    'PROJECT_JOIN_TRANSPOSE',
    'PROJECT_SET_OP_TRANSPOSE',
    'PROJECT_WINDOW_TRANSPOSE',
    'UNION_PULL_UP_CONSTANTS',
    'UNION_REMOVE',
    'UNION_TO_DISTINCT',
    'INTERSECT_TO_DISTINCT']
]

rule_groups = []
for rule_group in RULE_DIVISIONS:
    rules = []
    for rule_name in rule_group:
        sub_rules = calcite_rules[rule_name]
        rule_str = f'### Rule {rule_name}:\n{sub_rules}'
        rules.append(rule_str)
    rule_groups.append('\n\n'.join(rules))

CALCITE_OPERATOR_GROUPS = [['AGGREGATE'], ['CORRELATE'], ['FILTER'], ['INTERSECT', 'MINUS', 'UNION', 'SET_OP'], ['JOIN'], ['PROJECT'], ['SORT'], ['VALUES'], ['WINDOW']]

class MyModel:
    def __init__(self, model_args: t.Dict[str, str]):
        for k, v in model_args.items():
            setattr(self, k, v)
    
    async def gen_rewrites_from_cases(self, query: str, rewrite_cases_str: str) -> t.List[str]:
        messages = [{'role': 'system', 'content': self.GEN_CASE_REWRITE_SYS_PROMPT}, {'role': 'user', 'content': self.GEN_CASE_REWRITE_USER_PROMPT.format(sql=query, cases=rewrite_cases_str)}]

        for _ in range(2):
            response = await achat(messages)

            delimiter = 'Step 2:'
            delimiter_idx = response.find(delimiter)
            if delimiter_idx != -1:
                step2 = response[delimiter_idx + len(delimiter):]

                segs = re.split(r'Query Rewrite \d+:\s*"""', step2)
                rewrites = []
                for seg in segs[1:]:
                    end_idx = seg.rfind('"""')
                    if end_idx != -1:
                        seg = seg[:end_idx]
                    rewrites.append(seg.strip())
                return rewrites
        
        logging.warn(f"Failed to generate rewrites from retrieved rewrite cases: {response}")
        return []

    async def select_case_rules(self, rewrite_case: str, rules_str: str) -> t.List[str]:
        messages = [{'role': 'system', 'content': self.SELECT_CASE_RULE_SYS_PROMPT}, {'role': 'user', 'content': self.SELECT_CASE_RULE_USER_PROMPT.format(case=rewrite_case, rules=rules_str)}]

        for _ in range(2):
            response = await achat(messages, SELECT_CASE_RULE_MODEL)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    rule_names = eval(list_str)
                    return [rule_name.upper() for rule_name in rule_names if rule_name.upper() in calcite_rules]
                except:
                    pass
        return []

    async def select_rules_from_cases(self, retriever_res: List[NodeWithScore], normal_rules: List[t.Dict[str, str]], explore_rules: List[t.Dict[str, str]]) -> t.List[t.List[t.Dict[str, str]]]:
        normal_rule_names = [obj['name'] for obj in normal_rules]
        selected_rules = [[{'name': name, 'rewrite': calcite_rules[name]} for name in normal_rule_names]]

        selected_case_rules = defaultdict(float)
        task_names = []
        task_scores = []
        tasks = []

        for node in retriever_res:
            if node.id_ in case_rules:
                case_rule_names = case_rules[node.id_]
                for r in case_rule_names:
                    if r not in normal_rule_names:
                        selected_case_rules[r] += node.score
                continue
            
            for i, rules_str in enumerate(rule_groups):
                task_names.append((node.id_, i))
                task_scores.append(node.score)
                tasks.append(self.select_case_rules(node.text, rules_str))
        task_results = await asyncio.gather(*tasks)

        cur_case_rules: t.Dict[str, t.List[str]] = defaultdict(list)
        for (node_id, _), res in zip(task_names, task_results):
            cur_case_rules[node_id].extend(res)
        add_case_rules(cur_case_rules)

        for name, score, res in zip(task_names, task_scores, task_results):
            for r in res:
                if r not in normal_rule_names:
                    selected_case_rules[r] += score
        sorted_selected_case_rule_names = sorted(selected_case_rules.keys(), key=lambda x: selected_case_rules[x], reverse=True)
        logging.info('Selected Rules from Retrieved Rewrite Cases: ' + str(sorted_selected_case_rule_names))
        # sorted_selected_case_rule_names = sorted_selected_case_rule_names[:similarity_top_k]

        sorted_selected_case_rules = [{'name': name, 'rewrite': calcite_rules[name]} for name in sorted_selected_case_rule_names]
        selected_rules.append(sorted_selected_case_rules)

        left_explore_rules = [{'name': r['name'], 'rewrite': calcite_rules[r['name']]} for r in explore_rules if r['name'] not in sorted_selected_case_rule_names]
        selected_rules.append(left_explore_rules)
        return selected_rules

    async def gen_all_rewrites_from_cases(self, query: str, retriever_res: List[NodeWithScore], case_batch: int = 5) -> List[str]:
        tasks = []
        cases_suggestions = []
        for i in range(0, len(retriever_res), case_batch):
            cur_retriever_res = retriever_res[i: i + case_batch]
            cur_cases_str = '\n\n'.join([f'Case {j + 1}:\n"""{r.text}"""' for j, r in enumerate(cur_retriever_res)])
            tasks.append(self.gen_rewrites_from_cases(query, cur_cases_str))
        task_results = await asyncio.gather(*tasks)
        for cur_cases_suggestions in task_results:
            cases_suggestions.extend(cur_cases_suggestions)
        return cases_suggestions

    def cluster_rewrites(self, query: str, strategies_str: str, strategies: t.List[str]) -> t.List[t.List[str]]:
        messages = [{'role': 'system', 'content': self.CLUSTER_REWRITE_SYS_PROMPT}, {'role': 'user', 'content': self.CLUSTER_REWRITE_USER_PROMPT.format(sql=query, strategies=strategies_str)}]
        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    clusters = eval(list_str)
                    format_clusters = [[strategies[i - 1] for i in cluster if i >= 1 and i <= len(strategies)] for cluster in clusters]
                    clustered_strategy_num = sum([len(cluster) for cluster in format_clusters])
                    if clustered_strategy_num == len(strategies):
                        return format_clusters
                except:
                    pass
        logging.warn(f"Failed to cluster rewrite strategies: {response}")
        return [strategies]

    async def summarize_rewrites(self, query: str, strategies_str: str, cluster: t.List[str]) -> str:
        if len(cluster) == 1:
            return cluster[0]
        
        messages = [{'role': 'system', 'content': self.SUMMARIZE_REWRITE_SYS_PROMPT}, {'role': 'user', 'content': self.SUMMARIZE_REWRITE_USER_PROMPT.format(sql=query, strategies=strategies_str)}]
        response = await achat(messages)
        return response

    async def summarize_all_strategies(self, query: str, strategies: List[str]) -> List[str]:
        strategies_str = '\n\n'.join([f'Query Rewrite {i + 1}:\n"""{s}"""' for i, s in enumerate(strategies)])
        logging.info('Generated Rewrite Strategies:\n' + strategies_str)
        strategy_clusters = self.cluster_rewrites(query, strategies_str, strategies)

        tasks = []
        for cluster in strategy_clusters:
            cur_strategies_str = '\n\n'.join([f'Query Rewrite {j+1}:\n"""{r}"""' for j, r in enumerate(cluster)])
            tasks.append(self.summarize_rewrites(query, cur_strategies_str, cluster))
        task_results = await asyncio.gather(*tasks)
        return task_results

    async def gen_summarize_strategies(self, query: str, retriever_res: List[NodeWithScore], strategies: List[str], case_batch: int = 5) -> t.List[str]:
        cases_suggestions = await self.gen_all_rewrites_from_cases(query, retriever_res, case_batch=case_batch)
        all_strategies = strategies + cases_suggestions
        summarized_strategies = await self.summarize_all_strategies(query, all_strategies)
        return summarized_strategies

    def arrange_rule_sets(self, query: str, suggestions_str: str, rule_names: t.List[str], rules_str: str) -> t.List[t.List[str]]:
        rule_groups_dict = get_rule_sets(rule_names)
        if len(rule_groups_dict) == 0:
            return []
        rule_sets_str = '\n\n'.join([f'### {op} Operator Rules: ' + str(group).replace("'", '"') for op, group in rule_groups_dict.items()])
        messages = [{'role': 'system', 'content': self.ARRANGE_RULE_SETS_SYS_PROMPT}, {'role': 'user', 'content': self.ARRANGE_RULE_SETS_USER_PROMPT.format(sql=query, suggestions=suggestions_str, rule_sets=rule_sets_str, rules=rules_str)}]

        arranged_rule_sets = []
        for _ in range(2):
            response = chat(messages)
            
            res = re.findall(r'```python\s*(.+?)\s*```', response, re.I | re.DOTALL)
            for python_content in res:
                try:
                    cur_rule_names = eval(python_content)
                    arranged_rule_sets.append([r.upper() for r in cur_rule_names if r.upper() in rule_names])
                except:
                    pass
            if len(arranged_rule_sets) > 0:
                return arranged_rule_sets
        logging.warn(f"Failed to arrange selected rule sets: {response}")
        return []

    def arrange_rules(self, query: str, suggestions_str: str, selected_rules: t.List[t.Dict[str, str]]) -> t.List[str]:
        rules_str = '\n\n'.join([f'### Rule {r["name"]}:\n"""{r["rewrite"]}"""' for r in selected_rules])
        rule_names = [r['name'] for r in selected_rules]
        arranged_rule_sets: t.List[t.List[str]] = self.arrange_rule_sets(query, suggestions_str, rule_names, rules_str)
        logging.info(f'Arranged Rule Sets: {arranged_rule_sets}')
        arranged_rule_sets_str = '\n\n'.join([f'### Rule Sequence {i+1}: ' + str(seq).replace("'", '"') for i, seq in enumerate(arranged_rule_sets)])
        messages = [{'role': 'system', 'content': self.ARRANGE_RULES_SYS_PROMPT}, {'role': 'user', 'content': self.ARRANGE_RULES_USER_PROMPT.format(sql=query, suggestions=suggestions_str, rules=rules_str, rule_sequences=arranged_rule_sets_str)}]

        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    res = eval(list_str)
                    format_res = [rule_name.upper() for rule_name in res if rule_name.upper() in rule_names]
                    if len(format_res) * 2 > len(selected_rules):
                        return format_res
                except:
                    pass
        logging.warn(f"Failed to arrange selected rules: {response}")
        return rule_names

    def rearrange_rules(self, query: str, suggestions_str: str, selected_rules: t.List[t.Dict[str, str]], arranged_rules: t.List[str], used_rules: t.List[str]) -> t.List[str]:
        rules_str = '\n\n'.join([f'### Rule {r["name"]}:\n"""{r["rewrite"]}"""' for r in selected_rules])
        rule_names = [r['name'] for r in selected_rules]
        unused_rules = [r for r in arranged_rules if r not in used_rules]
        messages = [{'role': 'system', 'content': self.REARRANGE_RULES_SYS_PROMPT}, {'role': 'user', 'content': self.REARRANGE_RULES_USER_PROMPT.format(sql=query, suggestions=suggestions_str, rules=rules_str, arranged_rules=str(arranged_rules).replace("'", '"'), used_rules=str(used_rules).replace("'", '"'), unused_rules=str(unused_rules).replace("'", '"'))}]

        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    res = eval(list_str)
                    format_res = [rule_name.upper() for rule_name in res if rule_name.upper() in rule_names]
                    if len(format_res) * 2 > len(selected_rules):
                        return format_res
                except:
                    pass
        logging.warn(f"Failed to re-arrange selected rules: {response}")
        return rule_names

    def select_rules(self, query: str, suggestions_str: str, rules: t.List[t.Dict[str, str]]) -> t.List[t.Dict[str, str]]:
        rules_str = '\n\n'.join([f'### Rule {r["name"]}:\n"""{r["rewrite"]}"""' for i, r in enumerate(rules)])
        messages = [{'role': 'system', 'content': self.SELECT_RULES_SYS_PROMPT}, {'role': 'user', 'content': self.SELECT_RULES_USER_PROMPT.format(sql=query, suggestions=suggestions_str, rules=rules_str)}]

        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    rule_names = [r.upper() for r in eval(list_str)]
                    relevant_rules = []
                    for r in rules:
                        if r['name'] in rule_names:
                            relevant_rules.append(r)
                    return relevant_rules
                except:
                    pass
        logging.warn(f"Failed to select relevant rules: {response}")
        return []

    def select_arrange_rules(self, query: str, selected_rules: t.List[t.Dict[str, str]]) -> t.List[str]:
        rules_str = '\n\n'.join([f'### Rule {r["name"]}:\n"""{r["description"]}"""' for r in selected_rules])
        rule_names = [r['name'] for r in selected_rules]
        messages = [{'role': 'system', 'content': self.SELECT_ARRANGE_RULES_SYS_PROMPT}, {'role': 'user', 'content': self.SELECT_ARRANGE_RULES_USER_PROMPT.format(sql=query, rules=rules_str)}]

        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    res = eval(list_str)
                    format_res = [rule_name.upper() for rule_name in res if rule_name.upper() in rule_names]
                    return format_res
                except:
                    pass
        logging.warn(f"Failed to perform LLM-only rule-based rewrite: {response}")
        return []
    
    def rag_select_arrange_rules(self, query: str, selected_rules: t.List[t.Dict[str, str]], retrieved_rules: t.List[t.Dict[str, str]], retrieved_qas: t.List[NodeWithScore]) -> t.List[str]:
        rules_str = '\n\n'.join([f'### Rule {r["name"]}:\n"""{r["description"]}"""' for r in selected_rules])
        rule_names = [r['name'] for r in selected_rules]
        documents_str = '\n\n'.join([f'"""### Rule {r["name"]}:\n{r["description"]}"""' for r in retrieved_rules] + [f'"""{r.text}"""' for r in retrieved_qas])
        messages = [{'role': 'system', 'content': self.RAG_SELECT_ARRANGE_RULES_SYS_PROMPT}, {'role': 'user', 'content': self.RAG_SELECT_ARRANGE_RULES_USER_PROMPT.format(sql=query, documents=documents_str, rules=rules_str)}]

        for _ in range(2):
            response = chat(messages)
            
            prefix = '```python'
            suffix = '```'
            start_idx = response.find(prefix)
            end_idx = response.rfind(suffix)
            if start_idx != -1 and end_idx != -1:
                list_str = response[start_idx + len(prefix): end_idx].strip()
                try:
                    res = eval(list_str)
                    format_res = [rule_name.upper() for rule_name in res if rule_name.upper() in rule_names]
                    return format_res
                except:
                    pass
        logging.warn(f"Failed to perform LLM-only rule-based rewrite: {response}")
        return []

