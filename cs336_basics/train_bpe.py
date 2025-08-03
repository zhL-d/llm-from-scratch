from tokenizer import BPETokenizer
import time
import tracemalloc
    
def main():
    tracemalloc.start()
    start_time = time.perf_counter()

    """Example usage of the BPE tokenizer"""
    # Initialize bpe tokenizer
    tokenizer = BPETokenizer(
        special_tokens=["<|endoftext|>"], 
        log_file="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/gold.log",
        enable_logging=False,
        serialization=True,
        serialization_vocab_path= "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/serialization_vocab.json",
        serialization_merge_path= "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/serialization_merge.json"
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
            "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/training_data.txt", 
            vocab_size=500, # small_text is 263
            parallel=True
        )

        print(f"Vocabulary size: {len(vocab)}")
        print(f"Number of merges: {len(merges)}")
        print(f"First 5 merges: {merges[:5]}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error during traning: {e}")
    
    end_time = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Total time: {(end_time - start_time):.2f} seconds")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main()