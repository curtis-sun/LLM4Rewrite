import typing as t
import logging
from scipy import stats
import json
import os

from my_rewriter.config import CACHE_PATH
from my_rewriter.database import Database, DBArgs
from my_rewriter.rewrite import rewrite

def execute_rewrite(query: str, schema: str, db_args: DBArgs, rule_seq: t.List[str], rounds: int) -> t.Dict:
    create_tables = [x for x in schema.split(';') if x.strip() != '']
    res = rewrite(query, create_tables, rule_seq, rounds)

    db = Database(db_args)
    used_rules = [str(r) for r in res.rules]
    output_sql = str(res.sql)
    rewrite_time = int(res.time)
    output_cost = -1
    if output_sql != 'None':
        output_cost = db.cost_estimation(output_sql)
    res_dict = {'used_rules': used_rules, 'output_sql': output_sql, 'output_cost': output_cost, 'time': rewrite_time}
    logging.info(f'Rewrite Execution Results: {res_dict}')
    return res_dict

def compare(a: t.List[float], b: t.List[float], alternative: str = 'greater', threshold: float = 0.1) -> bool:
    _, p_value = stats.ttest_ind(a, b, alternative=alternative)
    return p_value < threshold

def actual_time(sql: str, db_args: DBArgs, timeout: int) -> t.Tuple[float, t.List[float]]:
    if sql not in db_args.cache:
        times = []
        for i in range(5):
            db = Database(db_args, timeout)
            latency = db.pgsql_actual_time(sql)
            if latency == -1:
                return float("inf"), [float("inf")] * 5
            if latency == timeout * 1000 and i == 0:
                times = [latency] * 5
                break
            times.append(latency)
        sorted_times = sorted(times)
        actual_time = sum(sorted_times[1:-1]) / 3
        db_args.cache[sql] = {'time': actual_time, 'times': times}
        with open(os.path.join(CACHE_PATH, f'{db_args.dbname}.jsonl'), 'a') as f:
            f.write(json.dumps({'sql': sql, 'time': actual_time, 'times': times}) + '\n')
    return db_args.cache[sql]['time'], db_args.cache[sql]['times']

def actual_time_once(sql: str, db_args: DBArgs, timeout: int) -> float:
    if sql not in db_args.cache:
        db = Database(db_args, timeout)
        latency = db.pgsql_actual_time(sql)
        if latency == -1:
            return float("inf")
        db_args.cache[sql] = {'time': latency}
        with open(os.path.join(CACHE_PATH, f'{db_args.dbname}.jsonl'), 'a') as f:
            f.write(json.dumps({'sql': sql, 'time': latency}) + '\n')
    return db_args.cache[sql]['time']