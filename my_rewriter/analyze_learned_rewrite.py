import os
from tqdm import tqdm
import time
from datetime import datetime
from prompts import *
from prettytable import PrettyTable
import logging
import json
import typing as t
from scipy import stats
import argparse
import re
from collections import defaultdict
import sys

sys.path.append('..')
from my_rewriter.database import DBArgs, Database
from my_rewriter.config import init_db_config
from my_rewriter.db_utils import compare, actual_time, actual_time_once

parser = argparse.ArgumentParser()
parser.add_argument('--compute_latency', action='store_true', required=False, help='whether to compute SQL latency')
parser.add_argument('--database', type=str, required=True)
parser.add_argument('--logdir', type=str, default='logs_learned_rewrite')
parser.add_argument('--large', action='store_true', required=False, help='whether to execute SQL queries on large database')
args = parser.parse_args()

pg_config = init_db_config(args.database)
pg_args = DBArgs(pg_config)

results = {}    
with open(f'{args.logdir}/{args.database}/res.jsonl', 'r') as fin:
    for line in fin.readlines():
        obj = json.loads(line)
        name = obj['name']
        results[name] = obj

def rewrite(input_cost: float, output_cost: float) -> bool:
    return input_cost > output_cost

def is_improved(t: t.Dict, idx: int, compute_latency: bool) -> bool:
    if rewrite(t['input_cost'], t['rewrites'][idx]['output_cost']):
        if compute_latency:
            if args.large:
                return t['input_latency'] > t['rewrites'][idx]['output_latency']
            else:
                return compare(t['input_var'], t['rewrites'][idx]['output_var'])
        else:
            return t['input_cost'] > t['rewrites'][idx]['output_cost']
    return False

def analyze(name: str) -> dict:
    obj = results[name]
    input_sql = obj['input_sql']
    if args.compute_latency:
        if args.large:
            input_latency = actual_time_once(input_sql, pg_args, 3600)
        else:
            input_latency, input_var = actual_time(input_sql, pg_args, 300)
    input_cost = float(obj['input_cost'])
    if input_cost == -1:
        input_cost = float("inf")
    
    output_sql = obj['output_sql']
    if output_sql == 'None':
        output_latency = input_latency
        if not args.large:
            output_var = [input_latency] * 5
    else:
        if args.compute_latency:
            if args.large:
                output_latency = actual_time_once(output_sql, pg_args, 3600)
            else:
                output_latency, output_var = actual_time(output_sql, pg_args, 300)
    output_cost = float(obj['output_cost'])
    if output_cost == -1:
        output_cost = float("inf")

    used_rules = obj['used_rules']
    rewrite_time = obj['rewrite_time']
    
    rewrite_obj = {'template': name, 'rewrite_time': rewrite_time, 'input_sql': input_sql, 'input_cost': input_cost, 'rewrites': [{'output_sql': output_sql, 'output_cost': output_cost, 'used_rules': used_rules}]}
    if args.compute_latency:
        rewrite_obj['input_latency'] = input_latency
        if not args.large:
            rewrite_obj['input_var'] = input_var
        rewrite_obj['rewrites'][0]['output_latency'] = output_latency
        if not args.large:
            rewrite_obj['rewrites'][0]['output_var'] = output_var
    return rewrite_obj

analyze_log_filename = f'{args.logdir}/{args.database}.log'
logging.basicConfig(filename=analyze_log_filename,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

if 'calcite' in args.database:
    DATASET = 'calcite'
elif 'tpch' in args.database:
    DATASET = 'tpch'
elif 'dsb' in args.database:
    DATASET = 'dsb'
else:
    DATASET = args.database

template_rewrites = []
if DATASET == 'calcite':
    queries_path = os.path.join('..', DATASET, f'{DATASET}.jsonl')
    with open(queries_path, 'r') as fin:
        for line in tqdm(fin.readlines()):
            obj = json.loads(line)
            name = sorted([x['name'] for x in obj['rewrites']])[0]

            rewrite_obj = analyze(name)
            template_rewrites.append(rewrite_obj)
else:
    queries_path = os.path.join('..', DATASET, 'queries')
    query_templates = os.listdir(queries_path)
    for template in tqdm(query_templates):
        max_idx = 1 if args.large else 2
        for idx in range(max_idx):
            query_filename = f'{queries_path}/{template}/{template}_{idx}.sql'
            content = open(query_filename, 'r').read()
            content = re.sub(r'--.*\n', '', content)
            queries = [q.strip() + ';' for q in content.split(';') if q.strip()]
            for j, _ in enumerate(queries):
                name = f'{template}_{idx}' if len(queries) == 1 else f'{template}_{idx}_{j}'

                rewrite_obj = analyze(name)
                template_rewrites.append(rewrite_obj)

input_attr = 'input_latency' if args.compute_latency else 'input_cost'
output_attr = 'output_latency' if args.compute_latency else 'output_cost'

table = PrettyTable(['Template', 'Input', 'Output', 'Rules'])
for t in template_rewrites:
    if is_improved(t, 0, args.compute_latency):
        table.add_row([t['template'], t[input_attr], t['rewrites'][0][output_attr], t['rewrites'][0]['used_rules']])
logging.info('Improvements:\n' + str(table))
logging.info(f'Improved {table.rowcount} out of {len(template_rewrites)} queries')

output_latencies = [t['rewrites'][0][output_attr] if rewrite(t['input_cost'], t['rewrites'][0]['output_cost']) else t[input_attr] for t in template_rewrites]

average_latency = sum(output_latencies) / len(output_latencies)
logging.info(f'Average: {average_latency}')
median_latency = sorted(output_latencies)[len(output_latencies) // 2]
logging.info(f'Median: {median_latency}')
latency_90th = sorted(output_latencies)[int(0.9 * len(output_latencies))]
logging.info(f'90th Percentile: {latency_90th}')
latency_95th = sorted(output_latencies)[int(0.95 * len(output_latencies))]
logging.info(f'95th Percentile: {latency_95th}')

input_latencies = [t[input_attr] for t in template_rewrites]
average_input_latency = sum(input_latencies) / len(input_latencies)
logging.info(f'Average Input: {average_input_latency}')
median_input_latency = sorted(input_latencies)[len(input_latencies) // 2]
logging.info(f'Median Input: {median_input_latency}')
input_latency_90th = sorted(input_latencies)[int(0.9 * len(input_latencies))]
logging.info(f'90th Percentile Input: {input_latency_90th}')
input_latency_95th = sorted(input_latencies)[int(0.95 * len(input_latencies))]
logging.info(f'95th Percentile Input: {input_latency_95th}')

average_rewrite = sum([t['rewrite_time'] for t in template_rewrites]) / len(template_rewrites)
logging.info(f'Average Total Time: {average_rewrite}')

if args.large:
    overall_latencies = [t['rewrite_time'] + o for t, o in zip(template_rewrites, output_latencies)]

    average_overall_latency = sum(overall_latencies) / len(overall_latencies)
    logging.info(f'Average Overall: {average_overall_latency}')
    median_overall_latency = sorted(overall_latencies)[len(overall_latencies) // 2]
    logging.info(f'Median Overall: {median_overall_latency}')
    overall_latency_90th = sorted(overall_latencies)[int(0.9 * len(overall_latencies))]
    logging.info(f'90th Percentile Overall: {overall_latency_90th}')
    overall_latency_95th = sorted(overall_latencies)[int(0.95 * len(overall_latencies))]
    logging.info(f'95th Percentile Overall: {overall_latency_95th}')
