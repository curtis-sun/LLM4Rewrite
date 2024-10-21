from typing import Dict, List, Optional, Tuple, cast
import logging
import math

from llama_index.core.schema import QueryBundle
from llama_index.core.settings import Settings

from rag.gen_sql_templates import gen_sql_templates
from rag.gen_rewrites_from_rules import gen_rewrites_from_rules, get_one_hot, NL_RULES, NORMAL_RULES
from rag.my_query_fusion_retriver import MyQueryFusionRetriever

class MyStructureRetriever(MyQueryFusionRetriever):
    def _get_queries(self, original_query: str) -> List[QueryBundle]:
        rewrites, matched_rules = gen_rewrites_from_rules(sql=original_query, schema=self.schema, fun=self._achat, verbose=self._verbose)

        for k, v in rewrites.items():
            self._queries[k] = v
        self._queries['matched_rules'] = matched_rules

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

        sql_template_with_embeddings = [{'query': q, 'embedding': Settings.embed_model.get_agg_embedding_from_queries([q])} for q in sql_templates]
        if len(sql_templates) == 0:
            sql_template_with_embeddings = [{'query': '', 'embedding': [0] * 1536}]
        synthesized_queries = []
        for t in sql_template_with_embeddings:
            embedding = [x / math.sqrt(2) for x in rules_one_hot + t['embedding']]
            synthesized_queries.append(QueryBundle(f'{original_query}\n{t["query"]}', embedding=embedding))

        return synthesized_queries