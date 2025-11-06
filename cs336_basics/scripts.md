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


  TRAINDATA_PATH=/Users/lucas/Documents/GitHub/stf-assignment1-basics/tests/fixtures/corpus.en OUTPUTS_PATH=/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/outputs VOCAB_SIZE=500 PRETOKEN_PROCS=4 uv run cs336_basics/train_bpe.py


  TRAINDATA_PATH=/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/owedataset/owt_valid.txt OUTPUTS_PATH=/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/outputs VOCAB_SIZE=1500 PRETOKEN_PROCS=4 uv run cs336_basics/train_bpe.py


CORPUS_PATH="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/smoke_test_fixture/sample_data/sample_TinyStoriesV2-GPT4-train_k10.txt" \
VOCAB_PATH="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/smoke_test_fixture/vocab_table/tiny_story/TinyStoriesV2-GPT4-train_serialization_vocab_20251003_134143.json" \
MERGE_PATH="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/smoke_test_fixture/vocab_table/tiny_story/TinyStoriesV2-GPT4-train_serialization_merge_20251003_134143.json" \
ARTIFACT_PATH="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/outputs/encoding" \
LOG_LEVEL=INFO \
uv run python cs336_basics/bpe_encoding.py


gcloud builds submit --tag eu.gcr.io/digital-proton-473814-m9/bpe-training:encoder-${GIT_SHA} .

gcloud ai custom-jobs create --region=europe-west3 --display-name=bpe-encode --config=vertex-job_encode.json

export GIT_SHA=$(git rev-parse --short HEAD)

gcloud builds submit --tag eu.gcr.io/digital-proton-473814-m9/bpe-training:trainer-${GIT_SHA} .

uv run pytest -k test_linear

uv run pytest --ignore=cs336_basics/owntest -k test_linear

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_linear

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_linear

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_rmsnorm

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_swiglu

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_rope

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_softmax_matches_pytorch

UV_NO_SYNC=1 uv run pytest --ignore=cs336_basics/owntest -k test_scaled_dot_product_attention


