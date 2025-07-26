import regex as re
import json, logging
from pathlib import Path

# logging.basicConfig(filename="/workspaces/stf-assignment1-basics/cs336_basics/gold_pairs.log", filemode="w", level=logging.INFO, format="%(message)s")

def dump_pair_count(pair_count: dict[tuple[bytes], int], merged_token: tuple[tuple[bytes], int], index: int):
    serial = { str(k): v for k, v in pair_count.items() }
    serial_merged_token = {str(merged_token[0]): merged_token[1]}
    logging.info(json.dumps({"step": index, "pair": serial, "merged": serial_merged_token}, ensure_ascii=False, sort_keys=True))

string = """\
low low low low low
lower lower widest widest widest
newest newest newest newest newest newest
"""

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
    
    def _pretokenize_and_count(self, docs: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes, ...], int]:
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
                pre_tokens = re.finditer(self.GPT_PAT, doc)
                pre_tokens_string = [match.group(0) for match in pre_tokens]
            else:
                pre_tokens_string = doc.split()
    
            for token in pre_tokens_string:
                token_bytes = token.encode("utf-8")
                token_tuple = tuple(token_bytes[i:i+1] for i in range(len(token_bytes)))
                token_counts[token_tuple] = token_counts.get(token_tuple, 0) + 1
            
        return token_counts
    
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
                pair_counts[token_tuple[i : i+2]] = pair_counts.get(token_tuple[i : i+2], 0) + count
        
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
    
        for k, v in pre_tokens.items():
            i = 0
            while i < len(k) - 1:
                if (k[i], k[i+1]) == merge_pair[0]:
                    k = k[0:i] + (k[i] + k[i+1],) + k[i+2:]
                i = i+1
            
            new_pretokens[k] = v
        
        return new_pretokens
    
    def _merge_pretokens_new(
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
    
    def train(
            self, 
            input_path: str, 
            vocab_size: int, 
        ) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
        """
        Train BPE tokenizer

        Args:
            input_path: Path to a text file with BPE tokenizer training data
            vocab_size: A positive integer that defines the maximum final vocabulary size 
              (including the initial byte vocabulary, vocabulary items produced from merging, and any special tokens)
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

        # Read training data
        input_file = Path(input_path)
        with input_file.open("r", encoding="utf-8") as file:
            text = file.read()
    
        # Removing special tokens and pre-tokenize
        cleaned_text = self._remove_special_tokens(text)
        pretoken_freqs = self._pretokenize_and_count(cleaned_text, gpt2_regex=True)

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
            pretoken_freqs = self._merge_pretokens_new(pretoken_freqs, merged_tuple)

        return self.vocab, self.merge         
    
def main():
    """Example usage of the BPE tokenizer"""
    # Initialize bpe tokenizer
    tokenizer = BPETokenizer(
        special_tokens=["<|endoftext|>"], 
        log_file="/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/gold.log"
    )
    
    # Train the tokenizer
    try:
        vocab, merges = tokenizer.train(
            "/Users/lucas/Documents/GitHub/stf-assignment1-basics/cs336_basics/training_data.txt", 
            vocab_size=320
        )

        print(f"Vocabulary size: {len(vocab)}")
        print(f"Number of merges: {len(merges)}")
        print(f"First 5 merges: {merge[:5]}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error during traning: {e}")

if __name__ == "__main__":
    main()

def init_vocab(special_tokens: list[str]) -> dict[int, bytes]:
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

    vocab : dict[int, bytes] = {x: bytes([x]) for x in range (256)}
    token_id_start = 256

    for i, special_token in enumerate(special_tokens):
        s_bytes = special_token.encode("utf-8")
        vocab[token_id_start + i] = s_bytes

    # vocab[special_token_id] = b'<|endoftext|>'

    # special_token_id = 256
    # vocab[special_token_id] = b'<|endoftext|>'
    return vocab

# init vocab
# vocab_test = init_vocab()
# print(vocab)

# # init pretokenization
# pretokens_freq : dict[tuple[bytes], int] = {}


def pretokenize_and_count(docs: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes], int]:
    token_count : dict[tuple[bytes], int] = {}

    for doc in docs:
        # pre_tokens : list[str] = []
        pre_tokens = None
        # use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
        if gpt2_regex:
            PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
            # pre_tokens = re.findall(PAT, doc)
            pre_tokens = re.finditer(PAT, doc)
        else:
            # TODO: change to iter
            pre_tokens = doc.split()

        for token in pre_tokens:
            # iter.match convert to string
            token_str = token.group(0)
            bytes_token = token_str.encode("utf-8")
            tuple_bytes_token = tuple(bytes_token[i : i+1] for i in range (len(bytes_token)))
            token_count[tuple_bytes_token] = token_count.get(tuple_bytes_token, 0) + 1
        
    return token_count

    # pre_tokens : list[str] = []
    # # use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
    # if gpt2_regex:
    #     PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
    #     # pre_tokens = re.findall(PAT, text)
    #     pre_tokens = re.finditer(PAT, text)
    # else:
    #     pre_tokens = text.split()
    
    # token_count : dict[tuple[bytes], int] = {}

    # for token in pre_tokens:
    #     bytes_token = token.encode("utf-8")
    #     tuple_bytes_token = tuple(bytes_token[i : i+1] for i in range (len(bytes_token)))
    #     token_count[tuple_bytes_token] = token_count.get(tuple_bytes_token, 0) + 1
    # return token_count



def merge(token_freqs : dict[tuple[bytes], int], index: int) -> tuple[tuple[bytes], int]:

    # here `freqs` refer to pretoken freqs
    def _count_mergetokens(freqs : dict[tuple[bytes], int]) -> dict[tuple[bytes], int]:

        merged_token_count : dict[tuple[bytes], int] = {}

        for k, v in freqs.items():
            for i in range(len(k)-1):
                merged_token_count[k[i : i+2]] = merged_token_count.get(k[i : i+2], 0) + v
        return merged_token_count
    
    # TODO: performance profile
    # here `freq` refer to merge adjcent token freqs
    def _pick_best_mergetoken(freqs: dict[tuple[bytes], int]) -> tuple[tuple[bytes], int]:
        # as-is
        return max(
            freqs.items(),
            key = lambda kv: (kv[1], kv[0])
        )
    
    # construct map: merged token: count
    mergetokens_freqs = _count_mergetokens(token_freqs)

   


    # find the most frequent adjcent tokens gram
    # break ties lexicographically
    best_merged_token = _pick_best_mergetoken(mergetokens_freqs)

    dump_pair_count(mergetokens_freqs, best_merged_token, index)

    return best_merged_token

# print("merged token statistic:", merge(pretokenize_and_count(string)))

# merge pretoken according to new merged token
def merge_pretoken(pre_tokens : dict[tuple[bytes], int], new_merged_token : tuple[tuple[bytes], int]) -> dict[tuple[bytes], int]:
    new_pretokens : dict[tuple[bytes], int] = {}

    for k, v in pre_tokens.items():
        i = 0
        while i < len(k) - 1:
            if (k[i], k[i+1]) == new_merged_token[0]:
                k = k[0:i] + (k[i] + k[i+1],) + k[i+2:]
            i = i+1
        
        new_pretokens[k] = v
    
    return new_pretokens

    # for k, v in pre_tokens.items():
    #     # # less than two items, no need to merge
    #     # if len(k) < 2:
    #     #     continue
    #     for i in range(len(k)-1):
    #         if (k[i], k[i+1]) == new_merged_token[0]:
    #             k = k[0:i] + (k[i] + k[i+1],) + k[i+2:]
        
    #     new_pretokens[k] = v
    
    # return new_pretokens
    # print("new pretoken", new_pretokens)

# merge_pretoken(pretokenization, merge(pretokenization))

# update vocab
def update_vocab(vocab : dict[int, bytes], merged_token : tuple[tuple[bytes], int]):
    # TODO: optimize point
    sorted_vocab = sorted(vocab.items(), reverse=True)
    new_index =  sorted_vocab[0][0] + 1
    
    k = merged_token[0]
    k = k[0] + k[1]

    vocab[new_index] = k

# update_vocab(vocab, merge(pretokenization))

# print("vocab_len:", len(vocab))

# input:
# text: use for train and tokenization
# vocab: original vocab
# num: merge number
# output:
# #print trained_vocab: trained vocab
# new_pretokens: new pretokens according to trained vocab
def bpe_train_tokenizer(text : str, vocab : dict[int, bytes], num: int) -> dict[tuple[bytes], int]:
    # pretokenize
    temp_pretokens_freq = pretokenize_and_count(text)

    for i in range(num):
        # pick best adjcent tokens to merge
        best_adjcent_tokens = merge(temp_pretokens_freq)
        # update vocabs
        update_vocab(vocab, best_adjcent_tokens)
        # update pretokens
        temp_pretokens_freq = merge_pretoken(temp_pretokens_freq, best_adjcent_tokens)
    
    return temp_pretokens_freq

# pretokens_freq = bpe_train_tokenizer(string, vocab, 6)
# print("pretokens:", pretokens_freq)
# print("vocab:", vocab)
# print("vocab length:", len(vocab))

# t: tuple[bytes, ...] = (b'h', b'e', b'l', b'l', b'o')

# # merge the first two bytes into one bytes object
# merged: tuple[bytes, ...] = (t[0] + t[1],) + t[2:]

# print(merged)  


def remove_special_tokens(text : str, special_tokens : list[str]) -> list[str]:
   stokens_escaped = [re.escape(stoken) for stoken in special_tokens]
   return re.split("|".join(stokens_escaped), text)


# input:
# input_path: str Path to a text file with BPE tokenizer training data.
# vocab_size: int A positive integer that defines the maximum final vocabulary size (including the
#   initial byte vocabulary, vocabulary items produced from merging, and any special tokens).
# special_tokens: list[str] A list of strings to add to the vocabulary. These special tokens do not otherwise affect BPE training.
# output:
# vocab: dict[int, bytes] The tokenizer vocabulary, a mapping from int (token ID in the vocabulary) to bytes (token bytes).
# merges: list[tuple[bytes, bytes]] A list of BPE merges produced from training. Each list item
#   is a tuple of bytes (<token1>, <token2>), representing that <token1> was merged with
#   <token2>. The merges should be ordered by order of creation.
def train_bpe(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    # init vocab
    vocab : dict[int, bytes] = init_vocab(special_tokens)
    # init merges
    merges : list[tuple[bytes, bytes]] = []

    # read training data
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    # print(text)

    # removing special tokens before pre-tokenization
    # Pre-tokenization
    #use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    # print("pretokens:", pretokens)
    # pretokens = pretokenize_and_count(text)

    for i in range(vocab_size - 256 - len(special_tokens)):
        # pick best adjcent tokens to merge
        merged_token = merge(pretokens, i)
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
        # update pretokens
        pretokens = merge_pretoken(pretokens, merged_token)
    
    return vocab, merges

# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 263, ["<|endoftext|>"])
# train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 263, ["<|endoftext|>"])

# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 320, ["<|endoftext|>"])

# print("vocab:", vocab)
# print("merges:", merges)