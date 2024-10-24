# Test query latency on DSB 10x.
python3 test.py --database dsb10 --logdir logs
python3 analyze.py --compute_latency --database dsb10 --logdir logs
python3 test_llm_only.py --database dsb10 --logdir logs_llm_only
python3 analyze_llm_only.py --compute_latency --database dsb10 --logdir logs_llm_only
python3 test.py --database dsb10 --logdir logs_gpt3
python3 analyze.py --compute_latency --database dsb10 --logdir logs_gpt3
python3 test_llm_only.py --database dsb10 --logdir logs_llm_only_gpt3
python3 analyze_llm_only.py --compute_latency --database dsb10 --logdir logs_llm_only_gpt3
python3 test_learned_rewrite.py --database dsb10 --logdir logs_learned_rewrite
python3 analyze_learned_rewrite.py --compute_latency --database dsb10 --logdir logs_learned_rewrite
# Test overall latency on DSB 50x.
python3 analyze.py --compute_latency --database dsb50 --logdir logs --large
python3 analyze.py --compute_latency --database dsb50 --logdir logs_gpt3 --large
python3 analyze_llm_only.py --compute_latency --database dsb50 --logdir logs_llm_only --large
python3 analyze_llm_only.py --compute_latency --database dsb50 --logdir logs_llm_only_gpt3 --large
python3 test_learned_rewrite.py --database dsb50 --logdir logs_learned_rewrite --large
python3 analyze_learned_rewrite.py --compute_latency --database dsb50 --logdir logs_learned_rewrite --large