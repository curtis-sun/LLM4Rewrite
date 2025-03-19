import logging
import sys
import os
import argparse
import re
import json
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

sys.path.append('..')
from my_rewriter.config import init_llms, init_db_config

parser = argparse.ArgumentParser()
parser.add_argument('--database', type=str, required=True)
parser.add_argument('--logdir', type=str, default='logs_llm_only')
args = parser.parse_args()

model_args = init_llms(args.logdir)
pg_config = init_db_config(args.database)

from my_rewriter.rag_rewrite import execute_rewrite
from my_rewriter.database import DBArgs, Database
from my_rewriter.my_utils import MyModel

with open('calcite_rules_selected_simple.jsonl', 'r') as fin:
    calcite_rules_simple = [json.loads(line) for line in fin.readlines()]

def llm_only_rewrite(query: str, schema: str, db_args: DBArgs, REWRITE_ROUNDS: int = 5):
    model = MyModel(model_args)
    rule_seq = model.select_arrange_rules(query, calcite_rules_simple)
    logging.info(f'Rule Sequence: {rule_seq}')
    rewrite_res = execute_rewrite(query, schema, db_args, rule_seq, REWRITE_ROUNDS)

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

schema_path = os.path.join('..', DATASET, 'create_tables.sql')
schema = open(schema_path, 'r').read()

if DATASET == 'calcite':
    queries_path = os.path.join('..', DATASET, f'{DATASET}.jsonl')
    with open(queries_path, 'r') as fin:
        for line in fin.readlines():
            obj = json.loads(line)
            query = obj['input_sql']
            name = sorted([x['name'] for x in obj['rewrites']])[0]
            # Remove all handlers associated with the root logger object.
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            log_filename = f'{LOG_DIR}/{name}.log'
            if os.path.exists(log_filename):
                continue
            logging.basicConfig(filename=log_filename,
                                filemode='a',
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.DEBUG)
            
            db = Database(pg_args)
            input_cost = db.cost_estimation(query)
            logging.info(f'Input Cost: {input_cost}')
            llm_only_rewrite(query, schema, pg_args, REWRITE_ROUNDS=REWRITE_ROUNDS)
else:
    queries_path = os.path.join('..', DATASET)
    query_templates = os.listdir(queries_path)
    for template in query_templates:
        for idx in range(2):
            query_filename = f'{queries_path}/{template}/{template}_{idx}.sql'
            content = open(query_filename, 'r').read()
            content = re.sub(r'--.*\n', '', content)
            queries = [q.strip() + ';' for q in content.split(';') if q.strip()]
            for j, query in enumerate(queries):
                # Remove all handlers associated with the root logger object.
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)
                log_filename = f'{LOG_DIR}/{template}_{idx}.log' if len(queries) == 1 else f'{LOG_DIR}/{template}_{idx}_{j}.log'
                if os.path.exists(log_filename):
                    continue
                logging.basicConfig(filename=log_filename,
                                    filemode='a',
                                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                    datefmt='%H:%M:%S',
                                    level=logging.DEBUG)
                
                db = Database(pg_args)
                input_cost = db.cost_estimation(query)
                logging.info(f'Input Cost: {input_cost}')
                llm_only_rewrite(query, schema, pg_args, REWRITE_ROUNDS=REWRITE_ROUNDS)
