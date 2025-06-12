import chromadb
import json
from typing import Any, Dict, List, Optional, Sequence, Union, cast, Tuple
import sys
import argparse
from tqdm import tqdm

from llama_index.core.schema import (
    BaseNode,
    IndexNode,
    NodeRelationship,
    NodeWithScore,
    RelatedNodeInfo,
    TextNode,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Settings

sys.path.append('..')
from my_rewriter.config import init_llms

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default='')
args = parser.parse_args()

# initialize text embedding model
init_llms(args.model)

# initialize client
db = chromadb.PersistentClient(path="./chroma_db")

# get collection
chroma_collection = db.get_or_create_collection("stackoverflow_summary")

# assign chroma as the vector_store to the context
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

def read_summaries_with_embedding(filename: str) -> Tuple[Dict[str, List[float]], Sequence[IndexNode]]:
    summary_to_embed_map = {}
    index_nodes = []
    with open(filename, 'r') as fin:
        for line in tqdm(fin.readlines()):
            obj = json.loads(line)
            myid = f'{obj["id"]}-{obj["answer_id"]}'
            summary = obj['summary']
            embedding = obj['embedding'] if args.model == '' else Settings.embed_model.get_query_embedding(summary)
            summary_to_embed_map[summary] = embedding
            text_node = TextNode(
                id_ = f'{myid}-summary',
                text=summary, 
                metadata={'references': str([myid])}, 
                excluded_embed_metadata_keys=['references'], 
                excluded_llm_metadata_keys=['references']
            )
            index_nodes.append(text_node)
    return summary_to_embed_map, index_nodes

summary_to_embed_map, index_nodes = read_summaries_with_embedding('stackoverflow-rewrite-query-optimization.jsonl')

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
            embedding = summary_to_embed_map[node.text]
            result = node.copy()
            result.embedding = embedding
            results.append(result)
        return results

index = MyVectorStoreIndex(index_nodes, storage_context=storage_context, show_progress=True)