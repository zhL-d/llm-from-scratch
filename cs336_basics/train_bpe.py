string = """\
low low low low low
lower lower widest widest widest
newest newest newest newest newest newest
"""

def init_vocab() -> dict[int, bytes]:
    vocab : dict[int, bytes] = {x: bytes([x]) for x in range (256)}
    special_token_id = 256
    vocab[special_token_id] = b'<|endoftext|>'
    return vocab

# init vocab
vocab = init_vocab()
# print(vocab)

# init pretokenization
pretokens_freq : dict[tuple[bytes], int] = {}


def pretokenize_and_count(text : str) -> dict[tuple[bytes], int]:
    pre_tokens : list[str] = string.split()
    token_count : dict[tuple[bytes], int] = {}

    for token in pre_tokens:
        bytes_token = token.encode("utf-8")
        tuple_bytes_token = tuple(bytes_token[i : i+1] for i in range (len(bytes_token)))
        token_count[tuple_bytes_token] = token_count.get(tuple_bytes_token, 0) + 1
    return token_count



def merge(token_freqs : dict[tuple[bytes], int]) -> tuple[tuple[bytes], int]:

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
    return _pick_best_mergetoken(mergetokens_freqs)

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

pretokens_freq = bpe_train_tokenizer(string, vocab, 6)
print("pretokens:", pretokens_freq)
# print("vocab:", vocab)

# t: tuple[bytes, ...] = (b'h', b'e', b'l', b'l', b'o')

# # merge the first two bytes into one bytes object
# merged: tuple[bytes, ...] = (t[0] + t[1],) + t[2:]

# print(merged)  


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
# def train_bpe(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]: