import psycopg2
import pymysql
import json
import logging
import typing as t
import os

from my_rewriter.config import CACHE_PATH

class DBArgs(object):

    def __init__(self, config: t.Dict[str, str]):
        self.dbtype = config['db']
        if self.dbtype == 'postgresql':
            self.host = config['host']
            self.port = config['port']
            self.user = config['user']
            self.password = config['password']
            self.dbname = config['dbname']
            self.driver = 'org.postgresql.Driver'
            self.jdbc = 'jdbc:postgresql://'
        else:
            raise NotImplementedError

        self.cache = {}
        with open(os.path.join(CACHE_PATH, f'{self.dbname}.jsonl'), 'r') as f:
            for line in f:
                obj = json.loads(line)
                self.cache[obj['sql']] = obj

class Database():

    def __init__(self, args: DBArgs, timeout: int = -1, enable_indexscan: bool = False):
        self.args = args
        self.conn = None
        self.timeout = timeout
        self.resetConn(timeout)
        self.enable_indexscan = enable_indexscan

    def resetConn(self, timeout: int = -1):
        if timeout > 0:
            self.conn = psycopg2.connect(database=self.args.dbname,
                                        user=self.args.user,
                                        password=self.args.password,
                                        host=self.args.host,
                                        port=self.args.port,
                                        options=f'-c statement_timeout={timeout}s')
        else:
            self.conn = psycopg2.connect(database=self.args.dbname,
                                        user=self.args.user,
                                        password=self.args.password,
                                        host=self.args.host,
                                        port=self.args.port)

    def exec_fetch(self, statement: str, one: bool = True):
        cur = self.conn.cursor()
        cur.execute(statement)
        if one:
            return cur.fetchone()
        return cur.fetchall()

    def execute_sql(self, sql: str):
        success = 0
        i = 0
        cnt = 3
        res = None
        logs = []
        cur = self.conn.cursor()
        while success == 0 and i < cnt:
            try:
                if not self.enable_indexscan:
                    cur.execute("SET enable_indexscan = off;")
                cur.execute(sql)
                success = 1
            except Exception as e:
                logs.append(e)
                if 'canceling statement due to statement timeout' in str(e):
                    return success, res, logs
            if success == 1:
                res = cur.fetchall()
            i = i + 1
        return success, res, logs

    def pgsql_cost_estimation(self, sql: str):
        success, res, logs = self.execute_sql('explain (FORMAT JSON) ' + sql)
        if success == 1:
            cost = res[0][0][0]['Plan']['Total Cost']
            return cost
        else:
            logging.error(f'Failed to execute pgsql_cost_estimation {sql}\n' + str(logs))
            return -1

    def pgsql_actual_time(self, sql: str):
        success, res, logs = self.execute_sql('explain (FORMAT JSON, analyze) ' + sql)
        if success == 1:
            return res[0][0][0]['Plan']['Actual Total Time']
        else:
            if 'canceling statement due to statement timeout' in str(logs):
                return self.timeout * 1000
            logging.error(f'Failed to execute pgsql_actual_time {sql}\n' + str(logs))
            return -1

    # query cost estimated by the optimizer
    def cost_estimation(self, sql: str):
        if self.args.dbtype == 'postgresql':
            return self.pgsql_cost_estimation(sql)
        else:
            raise NotImplementedError
