import chromadb
import json
from typing import Any, Dict, List, Optional, Sequence, Union, cast, Tuple
from collections import defaultdict
import math
import sys

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import (
    BaseNode,
    IndexNode,
    NodeRelationship,
    NodeWithScore,
    RelatedNodeInfo,
    TextNode,
)
from llama_index.embeddings.openai import OpenAIEmbedding

sys.path.append('..')
from rag.gen_rewrites_from_rules import NL_RULES, NORMAL_RULES

Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small"
)

# initialize client
db = chromadb.PersistentClient(path="./chroma_db")

# get collection
chroma_collection = db.get_or_create_collection("stackoverflow")

# assign chroma as the vector_store to the context
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

def read_sql_template_with_embedding(filename: str) -> Dict[str, List[float]]:
    sql_template_to_embed_map = {}
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            obj = json.loads(line)
            sql_template_to_embed_map[obj['sql_template']] = obj['embedding']
    return sql_template_to_embed_map

sql_template_to_embed_map = read_sql_template_with_embedding('stackoverflow-rewrite-sql-templates-embed-query-optimization.jsonl')
assert '' not in sql_template_to_embed_map

def get_one_hot(tot_rules: List[str], cur_rules: List[str]) -> List[int]:
    one_hot = [0] * len(tot_rules)
    for rule in cur_rules:
        if rule in tot_rules:
            one_hot[tot_rules.index(rule)] = 1
    return one_hot

def read_sql_with_embedding(filename: str) -> Dict[str, List[float]]:
    sql_to_embed_map = {}
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            obj = json.loads(line)
            one_hot = []
            one_hot.extend(get_one_hot(NL_RULES, obj['nl_rules']))
            one_hot.extend(get_one_hot(NORMAL_RULES, obj['rules']))
            one_cnt = sum(one_hot)
            if one_cnt > 0:
                one_hot = [x / math.sqrt(one_cnt) for x in one_hot]
            sql_to_embed_map[obj['sql']] = one_hot
    return sql_to_embed_map

sql_to_embed_map = read_sql_with_embedding('stackoverflow-rewrite-rules-query-optimization.jsonl')
assert '' not in sql_to_embed_map

def read_sql_with_sql_template(filename: str) -> Dict[str, List[str]]:
    sql_to_sql_template_map = defaultdict(list)
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            obj = json.loads(line)
            myid = f'{obj["id"]}-{obj["answer_id"]}'
            sql_templates = obj['sql_templates']
            for e in sql_templates:
                sql_to_sql_template_map[f'{myid}-{e["sql"]}'].append(e['template'])
    return sql_to_sql_template_map

sql_to_sql_template_map = read_sql_with_sql_template('stackoverflow-rewrite-sql-templates-query-optimization.jsonl')

def read_content_with_embedding(filename: str) -> Tuple[Dict[str, List[float]], Sequence[IndexNode]]:
    content_to_embed_map = {}
    index_nodes = []
    qa_cnt = 0
    sql_cnt = 0
    with open(filename, 'r') as fin:
        for line in fin.readlines():
            qa_cnt += 1
            obj = json.loads(line)
            myid = f'{obj["id"]}-{obj["answer_id"]}'
            summary = obj['summary']
            summary_embedding = obj['embedding']
            sql_structure_embedding_set = set()
            sqls = obj['question_body_sqls']
            if len(sqls) == 0:
                sqls = ['']
            for sql in sqls:
                sql_cnt += 1
                sql_embedding = sql_to_embed_map.get(sql, [0] * (len(NL_RULES) + len(NORMAL_RULES)))
                sql_templates = sql_to_sql_template_map.get(f'{myid}-{sql}', [])
                if len(sql_templates) == 0:
                    sql_templates = ['']
                for sql_template in sql_templates:
                    sql_template_embedding = sql_template_to_embed_map.get(sql_template, [0] * 1536)
                    sql_structure_embedding = sql_embedding + sql_template_embedding
                    embedding = [x / math.sqrt(3) for x in summary_embedding + sql_structure_embedding]
                    if str(sql_structure_embedding) in sql_structure_embedding_set:
                        continue
                    content = f'{summary}\n{sql}\n{sql_template}'
                    content_to_embed_map[content] = embedding
                    text_node = TextNode(
                        text=content, 
                        metadata={'references': str([myid])}, 
                        excluded_embed_metadata_keys=['references'], 
                        excluded_llm_metadata_keys=['references']
                    )
                    index_nodes.append(text_node)
                    sql_structure_embedding_set.add(str(sql_structure_embedding))
    print(f'Q&A Count: {qa_cnt}, SQL Count: {sql_cnt}, Node Count: {len(index_nodes)}')
    return content_to_embed_map, index_nodes

content_to_embed_map, index_nodes = read_content_with_embedding('stackoverflow-rewrite-query-optimization.jsonl')

class MyVectorStoreIndex(VectorStoreIndex):
    def _get_node_with_embedding(
        self,
        nodes: Sequence[BaseNode],
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """Get tuples of id, node, and embedding.

        Allows us to store these nodes in a vector store.
        Embeddings are called in batches.

        """
        results = []
        for node in nodes:
            embedding = content_to_embed_map[node.text]
            result = node.copy()
            result.embedding = embedding
            results.append(result)
        return results

index = MyVectorStoreIndex(index_nodes, storage_context=storage_context, show_progress=True)