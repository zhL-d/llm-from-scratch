from tokenizer import Tokenizer
import time
import tracemalloc
import os
import psutil
import contextlib

@contextlib.contextmanager
def perf_monitor(enabled: bool = True):
    if not enabled:
        yield {}
        return
    
   # Stat time and memory
    tracemalloc.start()
    start_time = time.perf_counter()
    
    try:
        yield {}
    finally:
        # Stat time and memory
        end_time = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory stat(rss)
        process = psutil.Process(os.getpid())
        rss_mem = process.memory_info().rss / (1024 * 1024)

        # Build report
        report = f"""
        Performence report
        -------------------------------
        Total time                      :{(end_time - start_time):.2f} seconds
        Peak memory managed by python   :{peak / 1024 / 1024:.2f} MB
        Total physical memory used(RSS) :{rss_mem:.2f} MB
        """

        print(report)

def main():
    with perf_monitor(enabled=False):
        # Init tokenizer
        tokenizer = Tokenizer(["<|endoftext|>"], False, "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/gold.log")
    
        # Training
        vocab, merges = tokenizer.train_bpe("/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/training_data.txt", 500, gpt2_regex=True, enable_parallel=True)

    # Build report
    report = f"""
        BPE Tokenizer Training report
        -------------------------------
        Vocabuary size                  :{len(vocab)}
        Number of merges                :{len(merges)}
        First 5 merges                  :{merges[:5]}
    """

    print(report)

if __name__ == "__main__":
    main()