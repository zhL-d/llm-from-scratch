import regex as re
import json, logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from typing import BinaryIO

small_text = """\
low low low low low
lower lower widest widest widest
newest newest newest newest newest newest
"""
GPT_PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

class BPETokenizer:
    """BPE tokenizer, byte-based"""

    GPT_PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

    def __init__(self, special_tokens: list[str] | None = None, log_file: str | str = None):
        """
        Initialize state of BPE tokenizer

        Args:
            special_tokens: Optional list of special tokens to add vocab
            log_file: Optional path of log file
        """
        self.special_tokens = special_tokens or []
        self.vocab = {}
        self.merge = []

        if log_file:
            self._set_up_logging(log_file)

    def _set_up_logging(self, log_file: str) -> None:
        logging.basicConfig(
            filename=log_file,
            filemode="w",
            level=logging.INFO,
            format="%(message)s"
        )

    def _initialize_vocab(self) -> dict[int, bytes]:
        """
        Initialize vocab using bytes and special tokens

        Args:
            special_tokens: Special tokens to reserve in vocab

        Returns:
            A dictionary mapping token IDs to bytes and special tokens

        Example:
            > init_vocab(["<|endoftext|>"])
            {0: b'\x00', 1: b'\x01', 2: b'\x02', 3: b'\x03', 4: b'\x04', 5: b'\x05', 6: b'\x06', 7: b'\x07', 8: b'\x08', 9: b'\t', 10: b'\n', ... , 255: b'\xff', 256: b'<|endoftext|>'}
        """

        vocab: dict[int, bytes] = {byte_value: bytes([byte_value]) for byte_value in range (256)}

        for i, special_token in enumerate(self.special_tokens):
            token_byte = special_token.encode("utf-8")
            vocab[256 + i] = token_byte

        return vocab
    
    @staticmethod
    def _pretokenize_and_count_static(docs: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes, ...], int]:
        """
        Pre-tokenize documents from input text and count pre-token frequencies

        Args:
            docs: List of docs from input text with special tokens removed
            gpt2_regex: Whether to use gpt2 regex pattern for pre-tokenization
        
        Returns:
            Dictionary mapping pretoken byte tuples to their freqencies
        """
        token_counts : dict[tuple[bytes], int] = {}
    
        for doc in docs:
            pre_tokens = None
            if gpt2_regex:
                # use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
                pre_tokens = re.finditer(GPT_PAT, doc)
                pre_tokens_string = [match.group(0) for match in pre_tokens]
            else:
                pre_tokens_string = doc.split()
    
            for token in pre_tokens_string:
                token_bytes = token.encode("utf-8")
                token_tuple = tuple(token_bytes[i:i+1] for i in range(len(token_bytes)))
                token_counts[token_tuple] = token_counts.get(token_tuple, 0) + 1
            
        return token_counts
    
    def _pretokenize_and_count(self, traindata_path: str, gpt2_regex: bool = False) -> dict[tuple[bytes, ...], int]:
        """
        Remove special tokens and pre-tokenize documents from input text and count pre-token frequencies

        Args:
            traindata_path: Path of training data
            gpt2_regex: Whether to use gpt2 regex pattern for pre-tokenization
        
        Returns:
            Dictionary mapping pretoken byte tuples to their freqencies
        """
        # Read training data
        p = Path(traindata_path)
        with p.open("r", encoding="utf-8") as file:
            text = file.read()

        # Remove special tokens
        docs = self._remove_special_tokens(text)

        token_counts : dict[tuple[bytes], int] = {}
    
        for doc in docs:
            pre_tokens = None
            if gpt2_regex:
                # use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
                pre_tokens = re.finditer(GPT_PAT, doc)
                pre_tokens_string = [match.group(0) for match in pre_tokens]
            else:
                pre_tokens_string = doc.split()
    
            for token in pre_tokens_string:
                token_bytes = token.encode("utf-8")
                token_tuple = tuple(token_bytes[i:i+1] for i in range(len(token_bytes)))
                token_counts[token_tuple] = token_counts.get(token_tuple, 0) + 1
            
        return token_counts
    
    def _remove_special_tokens(self, text: str) -> list[str]:
        """
        Remove special tokens from text before pre-tokenization

        Args:
            text: Input text
        
        Returns: 
            List of docs from text with special tokens removed
        """
        if not self.special_tokens:
            return [text]

        escaped_special_tokens = [re.escape(token) for token in self.special_tokens]
        return re.split("|".join(escaped_special_tokens), text)
    
    @staticmethod
    def _remove_special_tokens_static(text: str, special_tokens: list[str]) -> list[str]:
        """
        Remove special tokens from text before pre-tokenization

        Args:
            text: Input text
        
        Returns: 
            List of docs from text with special tokens removed
        """
        if not special_tokens:
            return [text]

        escaped_special_tokens = [re.escape(token) for token in special_tokens]
        return re.split("|".join(escaped_special_tokens), text)
    
    @staticmethod
    def _pretokenize_and_count_task(start: int, end: int, path: str, special_tokens: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes, ...], int]:
        """
        Remove special tokens and pretokenize chunk from training_data, count pretoken freqencies

        Args:
            start: Beginning index of training_data for this chunk
            end: Ending index of training_data text for this chunk
            path: Original training data path for tokenizer
            gpt2_regex: Whether to use gpt2 regex pattern for pre-tokenization
        Returns:
            Sub dictionary of pretoken and counts
        """
        with open(path, "rb") as f:
            f.seek(start)
            chunk = f.read(end - start).decode("utf-8", errors="ignore")
    
            cleaned_text = BPETokenizer._remove_special_tokens_static(chunk, special_tokens)
            pretoken_freqs = BPETokenizer._pretokenize_and_count_static(cleaned_text, gpt2_regex)
            return pretoken_freqs
    
    
    @staticmethod
    def find_chunk_boundaries(
        file: BinaryIO, 
        desired_num_chunks: int, 
        split_special_token: bytes
    ) -> list[int]:
        """
        Chunk the file into parts that can be counted independently.
        May return fewer chunks if the boundaries end up overlapping.
        """
        assert isinstance(split_special_token, bytes), (
            "Must represent special token as a bytestring"
        )
    
        # Get total file size in bytes
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
    
        chunk_size = file_size // desired_num_chunks
    
        # Initial guesses for chunk boundary locations, uniformly spaced
        # Chunks start on previous index, don't include last index
        chunk_boundaries = [i * chunk_size for i in range(desired_num_chunks + 1)]
        chunk_boundaries[-1] = file_size
    
        mini_chunk_size = 4096  # Read ahead by 4k bytes at a time
    
        for bi in range(1, len(chunk_boundaries) - 1):
            initial_position = chunk_boundaries[bi]
            file.seek(initial_position)  # Start at boundary guess
            while True:
                mini_chunk = file.read(mini_chunk_size)  # Read a mini chunk
    
                # If EOF, this boundary should be at the end of the file
                if mini_chunk == b"":
                    chunk_boundaries[bi] = file_size
                    break
    
                # Find the special token in the mini chunk
                found_at = mini_chunk.find(split_special_token)
                if found_at != -1:
                    chunk_boundaries[bi] = initial_position + found_at
                    break
                initial_position += mini_chunk_size
    
        # Make sure all boundaries are unique, but might be fewer than desired_num_chunks
        return sorted(set(chunk_boundaries))
        
    @staticmethod
    def _pretokenize_and_count_parallel(path: str, special_tokens: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes, ...], int]:
        """
        Parallelly pre-tokenize documents from training data and count pre-token frequencies

        Args:
            path: Path of training data
            gpt2_regex: Whether to use gpt2 regex pattern for pre-tokenization
        
        Returns:
            Dictionary mapping pretoken byte tuples to their freqencies
        """

        with open(path, "rb") as f:
            boundaries = BPETokenizer.find_chunk_boundaries(
                f, 4, "<|endoftext|>".encode("utf-8"))

            with ProcessPoolExecutor() as executor:
                futures = [executor.submit(BPETokenizer._pretokenize_and_count_task, start, end, path, special_tokens, gpt2_regex) for start, end in zip(boundaries[:-1], boundaries[1:])]

                pretoken_counts = {}

                for future in as_completed(futures):
                    for pretoken, count in future.result().items():
                        if pretoken in pretoken_counts:
                            pretoken_counts[pretoken] += count
                        else:
                            pretoken_counts[pretoken] = count
            
        return pretoken_counts
    
    # TODO: Optimize point
    def _count_adjacent_pairs(self, token_freqs: dict[tuple[bytes, ...], int]) -> dict[tuple[bytes, bytes], int]:
        """
        Build dictionary mapping adjacent pairs to freqencies from pretokens

        Args:
            token_freqs: Dictionary mapping pretokens mapping to freqencies
        
        Returns:
            Dictionary mapping adjacent pairs to freqencies
        """

        pair_counts: dict[tuple[bytes, bytes], int] = {}

        for token_tuple, count in token_freqs.items():
            for i in range(len(token_tuple) - 1):
                # pair_counts[token_tuple[i : i+2]] = pair_counts.get(token_tuple[i : i+2], 0) + count

                # Avoid creating slice overhead, can use package dis to check
                pair = (token_tuple[i], token_tuple[i + 1])
                pair_counts[pair] = pair_counts.get(pair, 0) + count
        return pair_counts
    
    def _find_best_merge_pair(self, pair_counts: dict[tuple[bytes, bytes], int]) -> tuple[tuple[bytes, bytes], int]:
        """
        Find best adjacent pair count 
        with the rule "deterministically break ties in pair frequency by preferring the lexicographically greater pair"

        Args:
            pair_counts: Dictionary of pairs frequencies
        
        Returns:
            Best pair count
        """
        if not pair_counts:
            raise ValueError("No pairs available for merging")

        return max(
            pair_counts.items(),
            key = lambda item: (item[1], item[0])
        )
    
    def _log_merge_steps(self, pair_counts: dict[tuple[bytes, bytes], int], 
                         best_pair: tuple[tuple[bytes, bytes], int], step: int) -> None:
        """
        Log merge steps for debugging purpose

        Args:
            pair_counts: Dictionary of pairs frenquencies in the current step
            best_pair: The best pair in the current step
            step: Current step
        """
        if logging.getLogger().handlers:
            # serialization: tuple -> string
            serializable_pair_count = {str(pair): count for pair, count in pair_counts.items()}
            serializable_best_pair = {str(best_pair[0]): best_pair[1]}

        log_data = {
            "step": step,
            "pair_counts": serializable_pair_count,
            "best_pair": serializable_best_pair
        }

        logging.info(json.dumps(log_data, ensure_ascii=False, sort_keys=True))
    
    # TODO: Optimize point
    def _merge_pretokens(
            self, 
            pre_tokens: dict[tuple[bytes, ...], int], 
            merge_pair: tuple[tuple[bytes, bytes], int]
    ) -> dict[tuple[bytes, ...], int]:
        """
        Build new pretokens by merging best pair in previous pretokens

        Args:
            pre_tokens: Dictionary mapping pretokens to frequencies
            merge_pair: Pair needed to merge
        
        Returns:
            New pretokens
        """
        new_pretokens: dict[tuple[bytes, ...], int] = {}
        target = merge_pair[0]
    
        for pretoken_tuple, freq in pre_tokens.items():
            i = 0
            new_pretoken: list[bytes] = []
            while i < len(pretoken_tuple):
                if i < len(pretoken_tuple) - 1 and (pretoken_tuple[i], pretoken_tuple[i + 1]) == target:
                    new_pretoken.append(pretoken_tuple[i] + pretoken_tuple[i+1])
                    i += 2 # Skip merge token
                else:
                    new_pretoken.append(pretoken_tuple[i])
                    i += 1
            
            new_pretokens[tuple(new_pretoken)] = freq
        
        return new_pretokens
    
    def _update_vocab(self, merge_pair: tuple[bytes, bytes]) -> None:
        """
        Insert merged pair to vocab

        Args:
            merge_pair: The pair that was merged
        """
        # Find the next available token id
        next_id = max(self.vocab.keys()) + 1
        merged_bytes = merge_pair[0] + merge_pair[1]
        self.vocab[next_id] = merged_bytes
    
    # def train_parallel(
    #         self, 
    #         input_path: str, 
    #         vocab_size: int, 
    #     ) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    #     """
    #     Train BPE tokenizer

    #     Args:
    #         input_path: Path to a text file with BPE tokenizer training data
    #         vocab_size: A positive integer that defines the maximum final vocabulary size 
    #           (including the initial byte vocabulary, vocabulary items produced from merging, and any special tokens)
    #     Returns:
    #         vocab: The tokenizer vocabulary, a mapping from int (token ID in the vocabulary) to bytes (token bytes)
    #         merges: A list of BPE merges produced from training. 
    #           Each list item is a tuple of bytes (<token1>, <token2>), 
    #           representing that <token1> was merged with <token2>. The merges should be ordered by order of creation.
        
    #     Raises:
    #         ValueError: if vocab size is too small
    #     """
    #     # Validate inputs
    #     if vocab_size < 256 + len(self.special_tokens):
    #         raise ValueError(f"vocab size must be at least {256 + len(self.special_tokens)}")
        
    #     # Initialize vocabulary
    #     self.vocab = self._initialize_vocab()

    #     # Read training data
    #     # input_file = Path(input_path)
    #     # with input_file.open("r", encoding="utf-8") as file:
    #     #     text = file.read()
    
    #     # Removing special tokens and pre-tokenize
    #     # cleaned_text = self._remove_special_tokens(text)
    #     # pretoken_freqs = self._pretokenize_and_count(cleaned_text, gpt2_regex=True)
    #     pretoken_freqs = BPETokenizer._pretokenize_and_count_parallel(input_path, self.special_tokens, True)

    #     # Peform BPE merge
    #     num_merges = vocab_size - 256 - len(self.special_tokens)
    
    #     for step in range(num_merges):
    #         # Buld pari counts
    #         pair_counts = self._count_adjacent_pairs(pretoken_freqs)

    #         # Find best merge pair
    #         merged_tuple= self._find_best_merge_pair(pair_counts)
        
    #         # Log the merge step
    #         self._log_merge_steps(pair_counts, merged_tuple, step)

    #         # Update vocabulary and merge
    #         self._update_vocab(merged_tuple[0])
    #         self.merge.append((merged_tuple[0][0], merged_tuple[0][1]))

    #         # Update pretokens
    #         pretoken_freqs = self._merge_pretokens(pretoken_freqs, merged_tuple)

    #     return self.vocab, self.merge     
    
    def train(
            self, 
            input_path: str, 
            vocab_size: int,
            parallel: bool 
        ) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
        """
        Train BPE tokenizer

        Args:
            input_path: Path to a text file with BPE tokenizer training data
            vocab_size: A positive integer that defines the maximum final vocabulary size 
              (including the initial byte vocabulary, vocabulary items produced from merging, and any special tokens)
            parallel: Whether to use parallel
        Returns:
            vocab: The tokenizer vocabulary, a mapping from int (token ID in the vocabulary) to bytes (token bytes)
            merges: A list of BPE merges produced from training. 
              Each list item is a tuple of bytes (<token1>, <token2>), 
              representing that <token1> was merged with <token2>. The merges should be ordered by order of creation.
        
        Raises:
            ValueError: if vocab size is too small
        """
        # Validate inputs
        if vocab_size < 256 + len(self.special_tokens):
            raise ValueError(f"vocab size must be at least {256 + len(self.special_tokens)}")
        
        # Initialize vocabulary
        self.vocab = self._initialize_vocab()

        # Build pretoken counts
        if parallel:
            pretoken_freqs = BPETokenizer._pretokenize_and_count_parallel(input_path, self.special_tokens, gpt2_regex=True)
        else:
            pretoken_freqs = self._pretokenize_and_count(input_path, gpt2_regex=True)

        # Peform BPE merge
        num_merges = vocab_size - 256 - len(self.special_tokens)
    
        for step in range(num_merges):
            # Buld pari counts
            pair_counts = self._count_adjacent_pairs(pretoken_freqs)

            # Find best merge pair
            merged_tuple= self._find_best_merge_pair(pair_counts)
        
            # Log the merge step
            self._log_merge_steps(pair_counts, merged_tuple, step)

            # Update vocabulary and merge
            self._update_vocab(merged_tuple[0])
            self.merge.append((merged_tuple[0][0], merged_tuple[0][1]))

            # Update pretokens
            pretoken_freqs = self._merge_pretokens(pretoken_freqs, merged_tuple)

        return self.vocab, self.merge 