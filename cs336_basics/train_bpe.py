import regex as re
import json, logging

logging.basicConfig(filename="/workspaces/stf-assignment1-basics/cs336_basics/gold_pairs.log", filemode="w", level=logging.INFO, format="%(message)s")

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

    def __init__(self, special_tokens: list[str] | None = None):
        """
        Initialize state of BPE tokenizer

        Args:
            special_tokens: List of special tokens to add vocab
        """
        self.special_tokens = special_tokens or []
        self.vocab = {}
        self.merge = []

    def _init_vocab(special_tokens: list[str]) -> dict[int, bytes]:
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

vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 320, ["<|endoftext|>"])

print("vocab:", vocab)
print("merges:", merges)