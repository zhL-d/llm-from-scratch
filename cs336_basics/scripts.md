python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_rust_optimize_final_output.txt

scalene /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py

uv run pytest tests/test_train_bpe.py


python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_perf_algo_baseline_withoutlog_parallel_output.txt