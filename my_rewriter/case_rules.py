import json
import typing as t
import jsonlines

from my_rewriter.config import CASE_RULES_PATH

case_rules: t.Dict[str, t.List[str]]  = {}
with open(CASE_RULES_PATH, 'r') as fin:
    for line in fin.readlines():
        obj = json.loads(line)
        case_rules[f'{obj["id"]}-{obj["answer_id"]}'] = obj["rules"]

def add_case_rules(cur_case_rules: t.Dict[str, t.List[str]]):
    update_case_rules = []
    for idx, rules in cur_case_rules.items():
        if idx not in case_rules:
            rules = list(set(rules))
            case_rules[idx] = rules
            qid, aid = idx.split('-')
            update_case_rules.append({'id': qid, 'answer_id': aid, 'rules': rules})
    if len(update_case_rules) > 0:
        with jsonlines.open(CASE_RULES_PATH, 'a') as fout:
            fout.write_all(update_case_rules)
    
        