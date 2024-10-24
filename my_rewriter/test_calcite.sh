# Test query latency on Calcite (uni).
python3 test.py --database calcite10 --logdir logs
python3 analyze.py --compute_latency --database calcite10 --logdir logs
python3 test_llm_only.py --database calcite10 --logdir logs_llm_only
python3 analyze_llm_only.py --compute_latency --database calcite10 --logdir logs_llm_only
python3 test.py --database calcite10 --logdir logs_gpt3
python3 analyze.py --compute_latency --database calcite10 --logdir logs_gpt3
python3 test_llm_only.py --database calcite10 --logdir logs_llm_only_gpt3
python3 analyze_llm_only.py --compute_latency --database calcite10 --logdir logs_llm_only_gpt3
python3 test_learned_rewrite.py --database calcite10 --logdir logs_learned_rewrite
python3 analyze_learned_rewrite.py --compute_latency --database calcite10 --logdir logs_learned_rewrite
# Test robustness of data distribution on Calcite (zipf).
python3 analyze.py --compute_latency --database calcite10zipf --logdir logs
python3 analyze.py --compute_latency --database calcite10zipf --logdir logs_gpt3
python3 analyze_llm_only.py --compute_latency --database calcite10zipf --logdir logs_llm_only
python3 analyze_llm_only.py --compute_latency --database calcite10zipf --logdir logs_llm_only_gpt3
python3 test_learned_rewrite.py --database calcite10zipf --logdir logs_learned_rewrite
python3 analyze_learned_rewrite.py --compute_latency --database calcite10zipf --logdir logs_learned_rewrite