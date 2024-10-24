# Test semantics-only retrieval.
python3 test.py --database calcite10 --logdir logs_ablation/semantics --index semantics
python3 analyze.py --compute_latency --database calcite10 --logdir logs_ablation/semantics
# Test naive RAG.
cp -R logs_ablation/semantics/ logs_ablation/semantics_no_steps
python3 adjust_no_steps.py --database calcite10 --logdir logs_ablation/semantics_no_steps
python3 analyze.py --compute_latency --database calcite10 --logdir logs_ablation/semantics_no_steps
# Test structure-only retrieval.
python3 test.py --database calcite10 --logdir logs_ablation/structure --index structure
python3 analyze.py --compute_latency --database calcite10 --logdir logs_ablation/structure
# Test different values of retrieval top-k.
python3 test.py --database calcite10 --logdir logs_topk/1 --topk 1
python3 analyze.py --compute_latency --database calcite10 --logdir logs_topk/1
python3 test.py --database calcite10 --logdir logs_topk/2 --topk 2
python3 analyze.py --compute_latency --database calcite10 --logdir logs_topk/2
python3 test.py --database calcite10 --logdir logs_topk/5 --topk 5
python3 analyze.py --compute_latency --database calcite10 --logdir logs_topk/5
python3 test.py --database calcite10 --logdir logs_topk/20 --topk 20
python3 analyze.py --compute_latency --database calcite10 --logdir logs_topk/20
# Test one-step LLM rewrite.
cp -R logs/calcite/ logs_ablation/no_steps/calcite
python3 adjust_no_steps.py --database calcite10 --logdir logs_ablation/no_steps
python3 analyze.py --compute_latency --database calcite10 --logdir logs_ablation/no_steps
# Test no rewrite reflection.
python3 analyze.py --compute_latency --database calcite10 --logdir logs --no_reflection