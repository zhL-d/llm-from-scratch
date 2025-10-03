python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_rust_optimize_final_output.txt

scalene /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py

uv run pytest tests/test_train_bpe.py


python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile/profile_cum_perfalgo_wolog_wop_output.txt



py-spy record -o baseline-pyspy.svg -- python -c \
'bash -lc "for i in {1..6}; do cs336_basics/train_bpe.py; done"'


py-spy record -o baseline-pyspy.svg -- bash -c 'for i in {1..6}; do python3 cs336_basics/train_bpe.py; done'

python -m cProfile -o cs336_basics/profile/baseline.prof cs336_basics/train_bpe.py
snakeviz baseline.prof


python3 -m cProfile -s cumtime /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/train_bpe.py > /Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/profile_cum_op_regex.txt

python3 -m cProfile -o cs336_basics/profile/archive/heap_pick_best_pair/profile_cum_op__pick_best_mergetoken.prof cs336_basics/train_bpe.py


TRAINDATA_PATH=tests/fixtures/corpus.en VOCAB_SIZE=500 uv run python -m cs336_basics.train_bpe


TRAINDATA_PATH=tests/fixtures/corpus.en VOCAB_SIZE=500 uv run python -m cProfile -s cumtime -m cs336_basics.train_bpe > cs336_basics/profile/profile_cum_envconfig.txt

bash -c ' export TRAINDATA_PATH="${{inputs.smokedata}}/corpus.en"; export OUTPUTS_PATH="${{outputs.smokeartifact}}"; export VOCAB_SIZE=500; pip install uv && uv sync --frozen && uv run python cs336_basics/train_bpe.py; 




Your job is still active. You may view the status of your job with the command

  $ gcloud ai custom-jobs describe projects/449740342413/locations/europe-west3/customJobs/5305134258170363904

or continue streaming the logs with the command

  $ gcloud ai custom-jobs stream-logs projects/449740342413/locations/europe-west3/customJobs/5305134258170363904


  bash -c ' export TRAINDATA_PATH="${{inputs.bpetrainlarge}}/owt_train.txt"; export OUTPUTS_PATH="${{outputs.bpetrainlarge}}"; export VOCAB_SIZE=32000; pip install uv && uv sync --frozen && uv run python cs336_basics/train_bpe.py; 




  gcloud ai custom-jobs create   --region=europe-west3   --display-name=bpe-training-job   --config=vertex-job.json