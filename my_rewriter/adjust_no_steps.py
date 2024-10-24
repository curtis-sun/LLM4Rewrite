import logging
import sys
import os
import typing as t
import re
from tqdm import tqdm
import argparse
import json
import itertools

from llama_index.core.schema import (
    BaseNode,
    TextNode,
    NodeWithScore
)

sys.path.append('..')
from my_rewriter.config import init_db_config, init_llms

parser = argparse.ArgumentParser()
parser.add_argument('--database', type=str, required=True)
parser.add_argument('--logdir', type=str, default='logs')
args = parser.parse_args()

model_args = init_llms(args.logdir)
pg_config = init_db_config(args.database)

from my_rewriter.db_utils import execute_rewrite
from my_rewriter.database import DBArgs, Database
from my_rewriter.my_utils import MyModel
from rag.gen_rewrites_from_rules import calcite_rules, rule_descriptions, RULE_FUNCTIONS

RULE_BATCH = 10
REWRITE_ROUNDS = 1
DATABASE = args.database

if 'calcite' in DATABASE:
    DATASET = 'calcite'
elif 'tpch' in DATABASE:
    DATASET = 'tpch'
elif 'dsb' in DATABASE:
    DATASET = 'dsb'
else:
    DATASET = DATABASE

LOG_DIR = os.path.join(args.logdir, DATASET)

pg_args = DBArgs(pg_config)
db = Database(pg_args)

my_rule_descriptions = {}
for i,func in enumerate(RULE_FUNCTIONS):
    assert func.__name__ not in my_rule_descriptions
    my_rule_descriptions[func.__name__] = rule_descriptions[i]

with open('calcite_rules_selected_simple.jsonl', 'r') as fin:
    calcite_rules_simple = [json.loads(line) for line in fin.readlines()]
    for rule in calcite_rules_simple:
        rule['description'] = calcite_rules[rule['name']]

def adjust_no_steps(query: str, name: str):
    log_filename = f'{LOG_DIR}/{name}.log'

    nl_rule_names = None
    normal_rule_names = None
    retriever_res = None
    retriever_res_idx = None
    log_lines = open(log_filename, 'r').readlines()
    res_cnt = 0
    for i, line in enumerate(log_lines):
        if 'root INFO Matched NL rewrite rules' in line:
            nl_rule_names = eval(line[line.find('['):])
        elif 'root INFO Matched Calcite normalization rules' in line:
            normal_rule_names = eval(line[line.find('['):])
        elif 'root INFO Retrieved Rewrite Cases' in line:
            retriever_res = eval(line[line.find('['):])
            retriever_res_idx = i
        elif 'root INFO Rewrite Execution Results' in line:
            res_cnt += 1
    if res_cnt == 1:
        return

    log_content = ''.join(log_lines[:retriever_res_idx + 1])
    with open(log_filename, 'w') as f:
        f.write(log_content)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=log_filename,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    
    nl_rules = [{'name': name, 'description': my_rule_descriptions[name]} for name in nl_rule_names]
    normal_rules = [{'name': name, 'description': calcite_rules[name]} for name in normal_rule_names]
    retrieved_rules = normal_rules + nl_rules
    
    logging.info('Start recipe-based rewrite...')
    model = MyModel(model_args)
    rule_seq = model.rag_select_arrange_rules(query, calcite_rules_simple, retrieved_rules=retrieved_rules, retrieved_qas=retriever_res)
    logging.info(f'Rule Sequence: {rule_seq}')
    rewrite_res = execute_rewrite(query, schema, pg_args, rule_seq, REWRITE_ROUNDS)

schema_path = os.path.join('..', DATASET, 'create_tables.sql')
schema = open(schema_path, 'r').read()

if DATASET == 'calcite':
    queries_path = os.path.join('..', DATASET, f'{DATASET}.jsonl')
    with open(queries_path, 'r') as fin:
        for line in fin.readlines():
            obj = json.loads(line)
            query = obj['input_sql']
            name = sorted([x['name'] for x in obj['rewrites']])[0]

            adjust_no_steps(query, name)
else:
    queries_path = os.path.join('..', DATASET, 'queries')
    query_templates = os.listdir(queries_path)
    for template in tqdm(query_templates):
        for idx in range(2):
            query_filename = f'{queries_path}/{template}/{template}_{idx}.sql'
            content = open(query_filename, 'r').read()
            content = re.sub(r'--.*\n', '', content)
            queries = [q.strip() + ';' for q in content.split(';') if q.strip()]
            for j, query in enumerate(queries):
                name = f'{template}_{idx}' if len(queries) == 1 else f'{template}_{idx}_{j}'
                
                adjust_no_steps(query, name)
