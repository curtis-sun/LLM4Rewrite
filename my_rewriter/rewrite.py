import os
import typing as t
import jpype as jp
import jpype.imports
from jpype.types import *

# zip -d LearnedRewrite.jar META-INF/DUMMY.SF
# zip -d LearnedRewrite.jar META-INF/DUMMY.DSA
''' Configure JAVA environment for JPype '''
classpath = ['CalciteRewrite/calcite_core_main_jar/calcite-core-1.38.0-SNAPSHOT.jar', 'CalciteRewrite/calcite_core_main_jar/calcite-linq4j-1.38.0-SNAPSHOT.jar', 'CalciteRewrite/calcite_core_main_jar/postgresql-42.7.3.jar']
local_lib_dir = 'CalciteRewrite/out/artifacts/LearnedRewrite_jar'
classpath.extend([os.path.join(local_lib_dir, jar) for jar in os.listdir(local_lib_dir)])

if not jp.isJVMStarted():
    jp.startJVM(jp.getDefaultJVMPath(), classpath=classpath)

from rewriter import Rewriter, RewriteResult, MyRules
from java.util import ArrayList
from learned import LearnedRewriter
from org.json.simple import JSONObject

def to_java_string(s: str) -> JString:
    return JString(s)

def to_java_bool(b: bool) -> JBoolean:
    return JBoolean(b)

def to_java_int(i: int) -> JInt:
    return JInt(i)

def to_java_list(lst: t.List) -> ArrayList:
    return ArrayList(lst)

def to_python_list(lst: ArrayList) -> t.List:
    return list(lst)

def match_normal_rules(query: str, create_tables: t.List[str], database: str = 'PostgreSQL', verbose: bool = True) -> t.List[t.Dict[str, str]]:
    return to_python_list(Rewriter.matchNormalRules(to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)))

def match_explore_rules(query: str, create_tables: t.List[str], database: str = 'PostgreSQL', verbose: bool = True) -> t.List[t.Dict[str, str]]:
    return to_python_list(Rewriter.matchExploreRules(to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)))

def match_all_rules(query: str, create_tables: t.List[str], database: str = 'PostgreSQL', verbose: bool = True) -> t.List[t.Dict[str, str]]:
    return to_python_list(Rewriter.matchAllRules(to_java_string(query), to_java_list(create_tables), to_java_string(database), to_java_bool(verbose)))

def rewrite(query: str, create_tables: t.List[str], rule_names: t.List[str], rounds: int, database: str = 'PostgreSQL') -> RewriteResult:
    return Rewriter.rewrite(to_java_string(query), to_java_list(create_tables), to_java_list(rule_names), to_java_int(rounds), to_java_string(database))

def learned_rewrite(query: str, create_tables: t.List[str], budget: int, host: str, port: str, user: str, password: str, dbname: str) -> JSONObject:
    return LearnedRewriter.learnedRewrite(to_java_string(query), to_java_list(create_tables), to_java_int(budget), to_java_string(host), to_java_string(port), to_java_string(user), to_java_string(password), to_java_string(dbname))

def get_normal_rules() -> t.List[str]:
    normal_rules = sorted([str(r) for r in MyRules.NORMAL_RULES.keySet()])
    return normal_rules
