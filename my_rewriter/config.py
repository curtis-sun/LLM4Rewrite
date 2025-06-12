from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike

CACHE_PATH = 'cache'
CASE_RULES_PATH = 'stackoverflow-rewrite-rules-query-optimization.jsonl'

def init_llms(model_type: str = '', load_model=True) -> dict[str, str]:
    if 'open' in model_type:
        if load_model:
            Settings.embed_model = HuggingFaceEmbedding(
                model_name='gte-Qwen2-1.5B-instruct',
                max_length=131072
            )
        embed_dim = 1536
    else:
        if load_model:
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small"
            )
        embed_dim = 1536
    
    if 'open' in model_type:
        if load_model:
            Settings.llm = OpenAILike(
                model="DeepSeek-R1-Distill-32B",
                api_key="",
                api_base="",
                context_window=131072,
                is_chat_model=True,
                tokenizer='DeepSeek-R1-Distill-32B'
            )
    elif 'gpt3' in model_type:
        if load_model:
            Settings.llm = OpenAI(
                model="gpt-3.5-turbo-0125"
            )
    else:
        if load_model:
            Settings.llm = OpenAI(
                model="gpt-4o"
            )
    from my_rewriter.prompts import GEN_CASE_REWRITE_SYS_PROMPT, GEN_CASE_REWRITE_USER_PROMPT, SELECT_CASE_RULE_SYS_PROMPT, SELECT_CASE_RULE_USER_PROMPT, CLUSTER_REWRITE_SYS_PROMPT, CLUSTER_REWRITE_USER_PROMPT, SUMMARIZE_REWRITE_SYS_PROMPT, SUMMARIZE_REWRITE_USER_PROMPT, SELECT_RULES_SYS_PROMPT, SELECT_RULES_USER_PROMPT, ARRANGE_RULE_SETS_SYS_PROMPT, ARRANGE_RULE_SETS_USER_PROMPT, ARRANGE_RULES_SYS_PROMPT, ARRANGE_RULES_USER_PROMPT, REARRANGE_RULES_SYS_PROMPT, REARRANGE_RULES_USER_PROMPT, SELECT_ARRANGE_RULES_SYS_PROMPT, SELECT_ARRANGE_RULES_USER_PROMPT, RAG_SELECT_ARRANGE_RULES_SYS_PROMPT, RAG_SELECT_ARRANGE_RULES_USER_PROMPT
    return {
        'GEN_CASE_REWRITE_SYS_PROMPT': GEN_CASE_REWRITE_SYS_PROMPT,
        'GEN_CASE_REWRITE_USER_PROMPT': GEN_CASE_REWRITE_USER_PROMPT,
        'SELECT_CASE_RULE_SYS_PROMPT': SELECT_CASE_RULE_SYS_PROMPT,
        'SELECT_CASE_RULE_USER_PROMPT': SELECT_CASE_RULE_USER_PROMPT,
        'CLUSTER_REWRITE_SYS_PROMPT': CLUSTER_REWRITE_SYS_PROMPT,
        'CLUSTER_REWRITE_USER_PROMPT': CLUSTER_REWRITE_USER_PROMPT,
        'SUMMARIZE_REWRITE_SYS_PROMPT': SUMMARIZE_REWRITE_SYS_PROMPT,
        'SUMMARIZE_REWRITE_USER_PROMPT': SUMMARIZE_REWRITE_USER_PROMPT,
        'SELECT_RULES_SYS_PROMPT': SELECT_RULES_SYS_PROMPT,
        'SELECT_RULES_USER_PROMPT': SELECT_RULES_USER_PROMPT,
        'ARRANGE_RULE_SETS_SYS_PROMPT': ARRANGE_RULE_SETS_SYS_PROMPT,
        'ARRANGE_RULE_SETS_USER_PROMPT': ARRANGE_RULE_SETS_USER_PROMPT,
        'ARRANGE_RULES_SYS_PROMPT': ARRANGE_RULES_SYS_PROMPT,
        'ARRANGE_RULES_USER_PROMPT': ARRANGE_RULES_USER_PROMPT,
        'REARRANGE_RULES_SYS_PROMPT': REARRANGE_RULES_SYS_PROMPT,
        'REARRANGE_RULES_USER_PROMPT': REARRANGE_RULES_USER_PROMPT,
        'SELECT_ARRANGE_RULES_SYS_PROMPT': SELECT_ARRANGE_RULES_SYS_PROMPT,
        'SELECT_ARRANGE_RULES_USER_PROMPT': SELECT_ARRANGE_RULES_USER_PROMPT,
        'RAG_SELECT_ARRANGE_RULES_SYS_PROMPT': RAG_SELECT_ARRANGE_RULES_SYS_PROMPT,
        'RAG_SELECT_ARRANGE_RULES_USER_PROMPT': RAG_SELECT_ARRANGE_RULES_USER_PROMPT,
        'EMBED_DIM': embed_dim
    }

def init_db_config(database: str) -> dict[str, str]:
    return {
        'host': '',
        'port': 5432,
        'user': '',
        'password': '',
        'dbname': database,
        'db': 'postgresql'
    }