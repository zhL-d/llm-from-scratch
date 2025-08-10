python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_rust_optimize_final_output.txt

scalene /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py

uv run pytest tests/test_train_bpe.py


python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile/profile_cum_perfalgo_wolog_wop_output.txt



py-spy record -o baseline-pyspy.svg -- python -c \
'bash -lc "for i in {1..6}; do cs336_basics/train_bpe.py; done"'


py-spy record -o baseline-pyspy.svg -- bash -c 'for i in {1..6}; do python3 cs336_basics/train_bpe.py; done'

python -m cProfile -o cs336_basics/profile/baseline.prof cs336_basics/train_bpe.py
snakeviz baseline.prof


python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_op__pick_best_mergetoken.txt