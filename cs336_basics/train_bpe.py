from tokenizer import BPETokenizer
    
def main():
    # import logging
    # logging.disable(logging.CRITICAL)

    """Example usage of the BPE tokenizer"""
    # Initialize bpe tokenizer
    tokenizer = BPETokenizer(
        special_tokens=["<|endoftext|>"], 
        log_file="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/gold.log",
        enable_logging=False
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

if __name__ == "__main__":
    main()