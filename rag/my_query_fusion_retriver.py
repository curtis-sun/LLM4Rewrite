import asyncio
from enum import Enum
from typing import Dict, List, Optional, Tuple, cast
from collections import defaultdict
import openai
import time
import logging
import math

from llama_index.core.async_utils import run_async_tasks
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.constants import DEFAULT_SIMILARITY_TOP_K
from llama_index.core.llms.utils import LLMType, resolve_llm
from llama_index.core.prompts import PromptTemplate
from llama_index.core.prompts.mixin import PromptDictType
from llama_index.core.retrievers import BaseRetriever, SummaryIndexRetriever, VectorIndexRetriever
from llama_index.core.schema import IndexNode, NodeWithScore, QueryBundle
from llama_index.core.settings import Settings
from llama_index.core.storage.docstore import BaseDocumentStore
from llama_index.core.base.llms.types import ChatMessage, LogProb, CompletionResponse

from rag.gen_sql_templates import gen_sql_templates
from rag.gen_rewrites_from_rules import gen_rewrites_from_rules, get_one_hot, NL_RULES, NORMAL_RULES


class FUSION_MODES(str, Enum):
    """Enum for different fusion modes."""

    RECIPROCAL_RANK = "reciprocal_rerank"  # apply reciprocal rank fusion
    RELATIVE_SCORE = "relative_score"  # apply relative score fusion
    DIST_BASED_SCORE = "dist_based_score"  # apply distance-based score fusion
    SIMPLE = "simple"  # simple re-ordering of results based on original scores


class MyQueryFusionRetriever(BaseRetriever):
    def __init__(
        self,
        docstore: BaseDocumentStore,
        qa_retriever: VectorIndexRetriever,
        embed_dim: int,
        schema: Optional[str] = None,
        llm: Optional[LLMType] = None,
        mode: FUSION_MODES = FUSION_MODES.SIMPLE,
        similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
        use_async: bool = True,
        verbose: bool = False,
        callback_manager: Optional[CallbackManager] = None,
        objects: Optional[List[IndexNode]] = None,
        object_map: Optional[dict] = None,
    ) -> None:
        self.docstore = docstore
        self.embed_dim = embed_dim
        self.schema = schema
        self.similarity_top_k = similarity_top_k
        self.mode = mode
        self.use_async = use_async

        self._retrievers = [qa_retriever]
        self._queries = dict()
        self._retriever_weights = [1.0]
        self._llm = (
            resolve_llm(llm, callback_manager=callback_manager) if llm else Settings.llm
        )
        super().__init__(
            callback_manager=callback_manager,
            object_map=object_map,
            objects=objects,
            verbose=verbose,
        )

    def _chat(self, messages: List[Dict]) -> str:
        chat_messages = [ChatMessage(**m) for m in messages]
        start = time.time()
        response = self._llm.chat(chat_messages)
        logging.debug({'messages': messages, 'response': response.message.content, 'time': time.time() - start})
        return response.message.content
    
    async def _achat(self, messages: List[Dict]) -> str:
        chat_messages = [ChatMessage(**m) for m in messages]
        start = time.time()
        try:
            response = await self._llm.achat(chat_messages)
        except (ConnectionResetError, openai.APIConnectionError):
            time.sleep(5)
            response = await self._llm.achat(chat_messages)
        logging.debug({'messages': messages, 'response': response.message.content, 'time': time.time() - start})
        return response.message.content

    def _get_queries(self, original_query: str) -> List[QueryBundle]:
        rewrites, matched_rules = gen_rewrites_from_rules(sql=original_query, schema=self.schema, fun=self._achat, verbose=self._verbose)

        for k, v in rewrites.items():
            self._queries[k] = v
        self._queries['matched_rules'] = matched_rules

        queries = []
        queries.extend([obj['rewrite'] for obj in rewrites['calcite'] if obj['type'] == 'normal'])
        queries.extend([obj['rewrite'] for obj in rewrites['nl']])

        if self._verbose:
            queries_str = "\n".join([f'Query {i + 1}: {q}' for i, q in enumerate(queries)])
            logging.info(f"Generated queries:\n{queries_str}")

        rules_one_hot: List[float] = []
        rules_one_hot.extend(get_one_hot(NL_RULES, matched_rules['nl']))
        rules_one_hot.extend(get_one_hot(NORMAL_RULES, matched_rules['calcite_normal']))
        one_cnt = sum(rules_one_hot)
        if one_cnt > 0:
            rules_one_hot = [x / math.sqrt(one_cnt) for x in rules_one_hot]

        sql_templates = list(gen_sql_templates(original_query).keys())
        self._queries['sql_templates'] = sql_templates

        if self._verbose:
            sql_templates_str = "\n".join([f'Template {i + 1}: {q}' for i, q in enumerate(sql_templates)])
            logging.info(f"Generated SQL templates:\n{sql_templates_str}")

        query_with_embeddings = [{'query': q, 'embedding': Settings.embed_model.get_query_embedding(q)} for q in queries]
        sql_template_with_embeddings = [{'query': q, 'embedding': Settings.embed_model.get_query_embedding(q)} for q in sql_templates]
        if len(sql_templates) == 0:
            sql_template_with_embeddings = [{'query': '', 'embedding': [0] * self.embed_dim}]
        synthesized_queries = []
        for q in query_with_embeddings:
            for t in sql_template_with_embeddings:
                embedding = [x / math.sqrt(3) for x in q['embedding'] + rules_one_hot + t['embedding']]
                synthesized_queries.append(QueryBundle(f'{q["query"]}\n{original_query}\n{t["query"]}', embedding=embedding))

        return synthesized_queries

    def _reciprocal_rerank_fusion(
        self, results: Dict[Tuple[str, int], List[NodeWithScore]]
    ) -> List[NodeWithScore]:
        """
        Apply reciprocal rank fusion.

        The original paper uses k=60 for best results:
        https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
        """

        retriever_num_queries = defaultdict(int)
        for query_tuple in results:
            retriever_num_queries[query_tuple[1]] += 1
        
        k = 60.0  # `k` is a parameter used to control the impact of outlier rankings.
        fused_scores = {}
        text_to_node = {}
        retriever_records = defaultdict(list)

        # compute reciprocal rank scores
        for query_tuple, nodes_with_scores in results.items():
            for rank, node_with_score in enumerate(
                sorted(nodes_with_scores, key=lambda x: x.score or 0.0, reverse=True)
            ):
                text = node_with_score.node.get_content()
                text_to_node[text] = node_with_score
                if text not in fused_scores:
                    fused_scores[text] = 0.0
                retriever_idx = query_tuple[1]
                cur_score = 1.0 / (rank + k) / retriever_num_queries[retriever_idx]
                fused_scores[text] += cur_score
                retriever_records[text].append((retriever_idx, cur_score))

        # sort results
        reranked_results = dict(
            sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        )

        # adjust node scores
        reranked_nodes: List[NodeWithScore] = []
        for text, score in reranked_results.items():
            reranked_nodes.append(text_to_node[text])
            reranked_nodes[-1].score = score

        # log retriever records
        reranked_retriever_records = []
        for n in reranked_nodes:
            reranked_retriever_records.append({'index': n.id_, 'retriever_records': retriever_records[n.node.get_content()]})
        logging.debug(f'Reranked Retriever Records: {reranked_retriever_records}')

        return reranked_nodes

    def _relative_score_fusion(
        self,
        results: Dict[Tuple[str, int], List[NodeWithScore]],
        dist_based: Optional[bool] = False,
    ) -> List[NodeWithScore]:
        """Apply relative score fusion."""
        # MinMax scale scores of each result set (highest value becomes 1, lowest becomes 0)
        # then scale by the weight of the retriever
        min_max_scores = {}
        for query_tuple, nodes_with_scores in results.items():
            if not nodes_with_scores:
                min_max_scores[query_tuple] = (0.0, 0.0)
                continue
            scores = [node_with_score.score for node_with_score in nodes_with_scores]
            if dist_based:
                # Set min and max based on mean and std dev
                mean_score = sum(scores) / len(scores)
                std_dev = (
                    sum((x - mean_score) ** 2 for x in scores) / len(scores)
                ) ** 0.5
                min_score = mean_score - 3 * std_dev
                max_score = mean_score + 3 * std_dev
            else:
                min_score = min(scores)
                max_score = max(scores)
            min_max_scores[query_tuple] = (min_score, max_score)

        retriever_num_queries = defaultdict(int)
        for query_tuple in results:
            retriever_num_queries[query_tuple[1]] += 1

        for query_tuple, nodes_with_scores in results.items():
            for node_with_score in nodes_with_scores:
                min_score, max_score = min_max_scores[query_tuple]
                # Scale the score to be between 0 and 1
                if max_score == min_score:
                    node_with_score.score = 1.0 if max_score > 0 else 0.0
                else:
                    node_with_score.score = (node_with_score.score - min_score) / (
                        max_score - min_score
                    )
                # Scale by the weight of the retriever
                retriever_idx = query_tuple[1]
                node_with_score.score *= self._retriever_weights[retriever_idx]
                # Divide by the number of queries
                node_with_score.score /= retriever_num_queries[retriever_idx]

        # Use a dict to de-duplicate nodes
        all_nodes: Dict[str, NodeWithScore] = {}

        # Sum scores for each node
        for nodes_with_scores in results.values():
            for node_with_score in nodes_with_scores:
                text = node_with_score.node.get_content()
                if text in all_nodes:
                    all_nodes[text].score += node_with_score.score
                else:
                    all_nodes[text] = node_with_score

        return sorted(all_nodes.values(), key=lambda x: x.score or 0.0, reverse=True)

    def _simple_fusion(
        self, results: Dict[Tuple[str, int], List[NodeWithScore]]
    ) -> List[NodeWithScore]:
        """Apply simple fusion."""
        # Use a dict to de-duplicate nodes
        all_nodes: Dict[str, NodeWithScore] = {}
        for nodes_with_scores in results.values():
            for node_with_score in nodes_with_scores:
                text = node_with_score.node.get_content()
                if text in all_nodes:
                    max_score = max(node_with_score.score, all_nodes[text].score)
                    all_nodes[text].score = max_score
                else:
                    all_nodes[text] = node_with_score

        return sorted(all_nodes.values(), key=lambda x: x.score or 0.0, reverse=True)

    def _run_nested_async_queries(
        self, queries: List[List[QueryBundle]]
    ) -> Dict[Tuple[str, int], List[NodeWithScore]]:
        tasks, task_queries = [], []
        for i, retriever in enumerate(self._retrievers):
            for query in queries[i]:
                tasks.append(retriever.aretrieve(query))
                task_queries.append((query.query_str, i))

        task_results = run_async_tasks(tasks)

        results = {}
        for query_tuple, query_result in zip(task_queries, task_results):
            results[query_tuple] = query_result

        return results

    async def _run_async_queries(
        self, queries: List[List[QueryBundle]]
    ) -> Dict[Tuple[str, int], List[NodeWithScore]]:
        tasks, task_queries = [], []
        for i, retriever in enumerate(self._retrievers):
            for query in queries[i]:
                tasks.append(retriever.aretrieve(query))
                task_queries.append((query.query_str, i))

        task_results = await asyncio.gather(*tasks)

        results = {}
        for query_tuple, query_result in zip(task_queries, task_results):
            results[query_tuple] = query_result

        return results

    def _run_sync_queries(
        self, queries: List[List[QueryBundle]]
    ) -> Dict[Tuple[str, int], List[NodeWithScore]]:
        results = {}
        for i, retriever in enumerate(self._retrievers):
            for query in queries[i]:
                results[(query.query_str, i)] = retriever.retrieve(query)

        return results

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        queries: List[List[QueryBundle]] = []
        synthesized_queries = self._get_queries(query_bundle.query_str)
        queries.append(synthesized_queries)

        if self.use_async:
            results = self._run_nested_async_queries(queries)
        else:
            results = self._run_sync_queries(queries)

        for (q, i) in results:
            node_id_to_score_map = {}
            for cur_node in results[(q, i)]:
                cur_node_ids = eval(cur_node.metadata['references'])
                for cur_node_id in cur_node_ids:
                    if cur_node_id in node_id_to_score_map:
                        node_id_to_score_map[cur_node_id] = max(node_id_to_score_map[cur_node_id], cur_node.get_score())
                    else:
                        node_id_to_score_map[cur_node_id] = cur_node.get_score()
            node_ids = node_id_to_score_map.keys()
            nodes = self.docstore.get_nodes(node_ids)
            node_with_scores = [NodeWithScore(node=n, score=node_id_to_score_map[id]) for id, n in zip(node_ids, nodes)]
            results[(q, i)] = node_with_scores

        if self.mode == FUSION_MODES.RECIPROCAL_RANK:
            return self._reciprocal_rerank_fusion(results)[: self.similarity_top_k]
        elif self.mode == FUSION_MODES.RELATIVE_SCORE:
            return self._relative_score_fusion(results)[: self.similarity_top_k]
        elif self.mode == FUSION_MODES.DIST_BASED_SCORE:
            return self._relative_score_fusion(results, dist_based=True)[
                : self.similarity_top_k
            ]
        elif self.mode == FUSION_MODES.SIMPLE:
            return self._simple_fusion(results)[: self.similarity_top_k]
        else:
            raise ValueError(f"Invalid fusion mode: {self.mode}")

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        queries: List[List[QueryBundle]] = []
        synthesized_queries = self._get_queries(query_bundle.query_str)
        queries.append(synthesized_queries)

        results = await self._run_async_queries(queries)

        for (q, i) in results:
            node_id_to_score_map = {}
            for cur_node in results[(q, i)]:
                cur_node_ids = eval(cur_node.metadata['references'])
                for cur_node_id in cur_node_ids:
                    if cur_node_id in node_id_to_score_map:
                        node_id_to_score_map[cur_node_id] = max(node_id_to_score_map[cur_node_id], cur_node.get_score())
                    else:
                        node_id_to_score_map[cur_node_id] = cur_node.get_score()
            node_ids = node_id_to_score_map.keys()
            nodes = self.docstore.get_nodes(node_ids)
            node_with_scores = [NodeWithScore(node=n, score=node_id_to_score_map[id]) for id, n in zip(node_ids, nodes)]
            results[(q, i)] = node_with_scores

        if self.mode == FUSION_MODES.RECIPROCAL_RANK:
            return self._reciprocal_rerank_fusion(results)[: self.similarity_top_k]
        elif self.mode == FUSION_MODES.RELATIVE_SCORE:
            return self._relative_score_fusion(results)[: self.similarity_top_k]
        elif self.mode == FUSION_MODES.DIST_BASED_SCORE:
            return self._relative_score_fusion(results, dist_based=True)[
                : self.similarity_top_k
            ]
        elif self.mode == FUSION_MODES.SIMPLE:
            return self._simple_fusion(results)[: self.similarity_top_k]
        else:
            raise ValueError(f"Invalid fusion mode: {self.mode}")
