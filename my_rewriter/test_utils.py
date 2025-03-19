import logging
import os

from llama_index.core.storage.docstore import SimpleDocumentStore

from my_rewriter.database import DBArgs, Database
from my_rewriter.rag_retrieve import rag_retrieve, rag_semantics_retrieve, rag_structure_retrieve
from my_rewriter.rag_rewrite import rag_rewrite

def test(name: str, query: str, schema: str, pg_args: DBArgs, model_args: dict[str, str], docstore: SimpleDocumentStore, LOG_DIR: str, RETRIEVER_TOP_K: int = 10, CASE_BATCH: int = 5, RULE_BATCH: int = 10, REWRITE_ROUNDS: int = 1, index: str = 'hybrid'):
    log_filename = f'{LOG_DIR}/{name}.log'
    if os.path.exists(log_filename):
        return
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=log_filename,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    db = Database(pg_args)
    input_cost = db.cost_estimation(query)
    logging.info(f'Input Cost: {input_cost}')
    if index == 'hybrid':
        res = rag_retrieve(query, schema, docstore, embed_dim=model_args['EMBED_DIM'], RETRIEVER_TOP_K=RETRIEVER_TOP_K)
    elif index == 'semantics':
        res = rag_semantics_retrieve(query, schema, docstore, RETRIEVER_TOP_K=RETRIEVER_TOP_K)
    elif index == 'structure':
        res = rag_structure_retrieve(query, schema, docstore, embed_dim=model_args['EMBED_DIM'], RETRIEVER_TOP_K=RETRIEVER_TOP_K)
    else:
        raise ValueError(f'Invalid index type: {index}')
    rag_rewrite(res['retriever_res'], res['rewrites'], query, schema, pg_args, model_args, CASE_BATCH=CASE_BATCH, RULE_BATCH=RULE_BATCH, REWRITE_ROUNDS=REWRITE_ROUNDS)