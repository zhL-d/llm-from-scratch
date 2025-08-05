from tokenizer import BPETokenizer
import time
import tracemalloc
import os
import psutil
import yaml
    
def main():
    # Time and memory stat
    tracemalloc.start()
    start_time = time.perf_counter()

    # Load config
    with open("cs336_basics/config_local.yaml", "r") as f:
        config = yaml.safe_load(f)

    """Example usage of the BPE tokenizer"""
    # Initialize bpe tokenizer
    tokenizer = BPETokenizer(
        special_tokens=config["special_tokens"], 
        log_file=config["log_file"],
        enable_logging=config["enable_logging"],
        serialization=config["serialization"],
        serialization_vocab_path= config["serialization_vocab_path"],
        serialization_merge_path= config["serialization_merge_path"]
    )
    
    # Train the tokenizer
    try:
        # vocab, merges = tokenizer.train(
        #     "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/training_data.txt", 
        #     vocab_size=500 # small_text is 263
        # )

        # vocab, merges = tokenizer.train_parallel(
        #     "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/training_data.txt", 
        #     vocab_size=500 # small_text is 263
        # )

        vocab, merges = tokenizer.train(
            config["traindata_path"], 
            vocab_size=config["vocab_size"], # small_text is 263
            parallel=config["parallel"]
        )

    except (FileNotFoundError, ValueError) as e:
        print(f"Error during traning: {e}")
    
    # Time and memory stat
    end_time = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Memory stat(rss)
    process = psutil.Process(os.getpid())
    rss_mem = process.memory_info().rss / (1024 * 1024)

    # Build report
    report = f"""
    BPE Tokenizer Training Report
    --------------------------------
    Vocabulary size                 :{len(vocab)}
    Number of merges                :{len(merges)}
    First 5 merges                  :{merges[:5]}


    Performance Summary
    --------------------------------
    Total time                      :{(end_time - start_time):.2f} seconds
    Peak memory managed by python   :{peak / 1024 / 1024:.2f} MB
    Total physical memory used(RSS) :{rss_mem:.2f} MB
    """

    print(report)

if __name__ == "__main__":
    main()