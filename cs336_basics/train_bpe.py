import regex as re
from dataclasses import dataclass, field
import json, logging
from collections import defaultdict

class Tokenizer:
    def __init__(self, special_tokens: list[str] | None = None):
        self.special_tokens = special_tokens or []
        self.vocab: dict[int, bytes] = {}
        self.merge: list[tuple[bytes, bytes]] = []
    
    @staticmethod
    def dump_pair_count(pair_count: dict[tuple[bytes], int], merged_token: tuple[tuple[bytes], int], index: int):
        serial = { str(k): v for k, v in pair_count.items() }
        serial_merged_token = {str(merged_token[0]): merged_token[1]}
        logging.info(json.dumps({"step": index, "pair": serial, "merged": serial_merged_token}, ensure_ascii=False, sort_keys=True))
    
    def init_vocab(self) -> dict[int, bytes]:
        vocab: dict[int, bytes] = {x: bytes([x]) for x in range (256)}
        token_id_start = 256
    
        for i, special_token in enumerate(self.special_tokens):
            s_bytes = special_token.encode("utf-8")
            vocab[token_id_start + i] = s_bytes
    
        return vocab
    
    def remove_special_tokens(self, text: str) -> list[str]:
        stokens_escaped = [re.escape(stoken) for stoken in self.special_tokens]
        return re.split("|".join(stokens_escaped), text)
    
    @staticmethod
    def pretokenize_and_count(docs: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes], int]:
        token_count : dict[tuple[bytes], int] = {}
    
        for doc in docs:
            pre_tokens = None
            # Use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
            if gpt2_regex:
                PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
                pre_tokens = re.finditer(PAT, doc)
            else:
                # TODO: change to iter
                pre_tokens = doc.split()
    
            for token in pre_tokens:
                if gpt2_regex:
                    # iter.match convert to string
                    token_str = token.group(0)
                else:
                    token_str = token
                bytes_token = token_str.encode("utf-8")
                
                tuple_bytes_token = tuple(bytes_token[i : i+1] for i in range (len(bytes_token)))
                token_count[tuple_bytes_token] = token_count.get(tuple_bytes_token, 0) + 1
            
        return token_count
    
    @staticmethod
    def build_paircount_and_cache(
        pretokens : dict[tuple[bytes, ...], int]
    ) -> tuple[
        dict[tuple[bytes], int], 
        dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ]:
    
        pair_count: dict[tuple[bytes], int] = {}
        cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]] = defaultdict(set)
    
        for k, v in pretokens.items():
            for i in range(len(k)-1):
                pair_count[k[i : i+2]] = pair_count.get(k[i : i+2], 0) + v
    
                cache[k[i : i+2]].add((k, v))
    
        return pair_count, cache
    
    @staticmethod
    def _pick_best_mergetoken(pair_count: dict[tuple[bytes], int]) -> tuple[tuple[bytes], int]:
        try:
            return max(
                pair_count.items(),
                key = lambda kv: (kv[1], kv[0])
            )
        except Exception as e:

        # Log or print the freqs that caused the failure
            print("Error picking best token, pair_count was:", pair_count)
            raise
    
    @staticmethod
    def _build_new_pretoken(
        old_pretoken: tuple[tuple[bytes, ...], int], 
        best_paircount: tuple[bytes, ...]
        ) ->  tuple[tuple[bytes, ...], int]:
    
        new_pretoken_pair = ()
        old_pretoken_pair = old_pretoken[0]
        best_pair = best_paircount
        i = 0
    
        while i < len(old_pretoken_pair)-1:
            if old_pretoken_pair[i : i+2] == best_pair:
                new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i] + old_pretoken_pair[i+1],)
    
                if i == len(old_pretoken_pair)-3:
                    new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i+2],)
    
                i = i+2
            else:
                new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i],)
    
                if i == len(old_pretoken_pair)-2:
                    new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i+1],)
    
                i = i+1
        
        new_pretoken = (new_pretoken_pair, old_pretoken[1])
    
        return new_pretoken
    
    @staticmethod
    def _delete_old_contribution(
        pretoken: tuple[tuple[bytes, ...], int], 
        pair_count: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

        pretoken_pair = pretoken[0]
        pretoken_count = pretoken[1]
    
        for i in range (len(pretoken_pair)-1):
            pair = pretoken_pair[i : i+2]
    
            pair_count[pair] = pair_count[pair] - pretoken_count
            if pair_count[pair] == 0:
                del pair_count[pair]
    
            reversed_cache[pair].discard(pretoken)
            if not reversed_cache[pair]:
                del reversed_cache[pair]
        
        return pair_count, reversed_cache
    
    @staticmethod
    def _add_new_contribution(
        pretoken: tuple[tuple[bytes, ...], int], 
        pair_count: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

        reversed_cache = defaultdict(set, reversed_cache)
        pretoken_pair = pretoken[0]
        pretoken_count = pretoken[1]
    
        for i in range (len(pretoken_pair)-1):
            pair = pretoken_pair[i : i+2]
    
            pair_count[pair] = pair_count.get(pair, 0) + pretoken_count
    
            reversed_cache[pair].add(pretoken)
        
        return pair_count, reversed_cache

    @staticmethod
    def merge_new(
        pair_counts: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]],
        best_pair: tuple[bytes, ...]
    ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

        affected_pretokens = reversed_cache[best_pair].copy()
    
        for old_pretoken in affected_pretokens:
            new_pretoken = Tokenizer._build_new_pretoken(old_pretoken, best_pair)
    
            # Update, delete old pretoken contribution
            pair_counts, reversed_cache = Tokenizer._delete_old_contribution(old_pretoken, pair_counts, reversed_cache)
            # update, add new pretoken contrbution
            pair_counts, reversed_cache = Tokenizer._add_new_contribution(new_pretoken, pair_counts, reversed_cache)

        return pair_counts, reversed_cache
    
    # Update vocab
    def update_vocab(self, best_pair: tuple[tuple[bytes], int]):
        # TODO: optimize point
        sorted_vocab = sorted(self.vocab.items(), reverse=True)
        new_index =  sorted_vocab[0][0] + 1
        
        k = best_pair[0]
        k = k[0] + k[1]
    
        self.vocab[new_index] = k
        
    def train_bpe(self, input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
        # Init vocab
        vocab: dict[int, bytes] = init_vocab(special_tokens)
        # Init merges
        merges: list[tuple[bytes, bytes]] = []
    
        # Read training data
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
    
        # Removing special tokens and pre-tokenization
        pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    
        # Build the first pair count and cache(pair to corresponding pretokens)
        pair_counts, reversed_cache = build_paircount_and_cache(pretokens)
    
        for i in range(vocab_size - 256 - len(special_tokens)):
            # Pick best adjcent tokens to merge
            best_pair = _pick_best_mergetoken(pair_counts)
    
            # Log pair counts, best pair and step
            dump_pair_count(pair_counts, best_pair, i)
    
            # Update pair counts and cache
            pair_counts,  reversed_cache = merge_new(pair_counts, reversed_cache, best_pair[0])
    
            # TODO: optimize point, insert vocab and merges two times
            # Update vocabs
            update_vocab(vocab, best_pair)
            # Update merges
            merges.append((best_pair[0][0], best_pair[0][1]))
        
        return vocab, merges

logging.basicConfig(filename="/workspaces/stf-assignment1-basics/cs336_basics/feature_pair.log", filemode="w", level=logging.INFO, format="%(message)s")

import json, logging

# NEED
def dump_pair_count(pair_count: dict[tuple[bytes], int], merged_token: tuple[tuple[bytes], int], index: int):
    serial = { str(k): v for k, v in pair_count.items() }
    serial_merged_token = {str(merged_token[0]): merged_token[1]}
    logging.info(json.dumps({"step": index, "pair": serial, "merged": serial_merged_token}, ensure_ascii=False, sort_keys=True))


string = """\
low low low low low
lower lower widest widest widest
newest newest newest newest newest newest
"""
# NEED
def init_vocab(special_tokens : list[str]) -> dict[int, bytes]:
    vocab : dict[int, bytes] = {x: bytes([x]) for x in range (256)}
    token_id_start = 256

    for i, special_token in enumerate(special_tokens):
        s_bytes = special_token.encode("utf-8")
        vocab[token_id_start + i] = s_bytes

    return vocab


# NEED
def pretokenize_and_count(docs: list[str], gpt2_regex: bool = False) -> dict[tuple[bytes], int]:
    token_count : dict[tuple[bytes], int] = {}

    for doc in docs:
        pre_tokens = None
        # Use a regex-based pre-tokenizer (used by GPT-2; Radford et al., 2019)
        if gpt2_regex:
            PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
            pre_tokens = re.finditer(PAT, doc)
        else:
            # TODO: change to iter
            pre_tokens = doc.split()

        for token in pre_tokens:
            if gpt2_regex:
                # iter.match convert to string
                token_str = token.group(0)
            else:
                token_str = token
            bytes_token = token_str.encode("utf-8")
            
            tuple_bytes_token = tuple(bytes_token[i : i+1] for i in range (len(bytes_token)))
            token_count[tuple_bytes_token] = token_count.get(tuple_bytes_token, 0) + 1
        
    return token_count

# NEED
# Update vocab
def update_vocab(vocab : dict[int, bytes], merged_token : tuple[tuple[bytes], int]):
    # TODO: optimize point
    sorted_vocab = sorted(vocab.items(), reverse=True)
    new_index =  sorted_vocab[0][0] + 1
    
    k = merged_token[0]
    k = k[0] + k[1]

    vocab[new_index] = k


# NEED
def remove_special_tokens(text: str, special_tokens: list[str]) -> list[str]:
   stokens_escaped = [re.escape(stoken) for stoken in special_tokens]
   return re.split("|".join(stokens_escaped), text)







# NEED
def build_paircount_and_cache(
        pretokens : dict[tuple[bytes, ...], int]
    ) -> tuple[
        dict[tuple[bytes], int], 
        dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ]:
    
    pair_count: dict[tuple[bytes], int] = {}
    cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]] = defaultdict(set)

    for k, v in pretokens.items():
        for i in range(len(k)-1):
            pair_count[k[i : i+2]] = pair_count.get(k[i : i+2], 0) + v

            cache[k[i : i+2]].add((k, v))

    return pair_count, cache

# NEED
def _build_new_pretoken(
        old_pretoken: tuple[tuple[bytes, ...], int], 
        # best_paircount: tuple[tuple[bytes, ...], int]
        best_paircount: tuple[bytes, ...]
        ) ->  tuple[tuple[bytes, ...], int]:
    
    new_pretoken_pair = ()
    old_pretoken_pair = old_pretoken[0]
    best_pair = best_paircount
    i = 0

    while i < len(old_pretoken_pair)-1:
        if old_pretoken_pair[i : i+2] == best_pair:
            new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i] + old_pretoken_pair[i+1],)

            if i == len(old_pretoken_pair)-3:
                new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i+2],)

            i = i+2
        else:
            new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i],)

            if i == len(old_pretoken_pair)-2:
                new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i+1],)

            i = i+1
    
    new_pretoken = (new_pretoken_pair, old_pretoken[1])

    return new_pretoken

# NEED
def _delete_old_contribution(
        pretoken: tuple[tuple[bytes, ...], int], 
        pair_count: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

    pretoken_pair = pretoken[0]
    pretoken_count = pretoken[1]

    for i in range (len(pretoken_pair)-1):
        pair = pretoken_pair[i : i+2]

        pair_count[pair] = pair_count[pair] - pretoken_count
        if pair_count[pair] == 0:
            del pair_count[pair]

        reversed_cache[pair].discard(pretoken)
        if not reversed_cache[pair]:
            del reversed_cache[pair]
    
    return pair_count, reversed_cache

# NEED
def _add_new_contribution(
        pretoken: tuple[tuple[bytes, ...], int], 
        pair_count: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

    reversed_cache = defaultdict(set, reversed_cache)
    pretoken_pair = pretoken[0]
    pretoken_count = pretoken[1]

    for i in range (len(pretoken_pair)-1):
        pair = pretoken_pair[i : i+2]

        pair_count[pair] = pair_count.get(pair, 0) + pretoken_count

        reversed_cache[pair].add(pretoken)
    
    return pair_count, reversed_cache

# NEED
def merge_new(
        pair_counts: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]],
        best_pair: tuple[bytes, ...]
    ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

    affected_pretokens = reversed_cache[best_pair].copy()

    for old_pretoken in affected_pretokens:
        new_pretoken = _build_new_pretoken(old_pretoken, best_pair)

        # Update, delete old pretoken contribution
        pair_counts, reversed_cache = _delete_old_contribution(old_pretoken, pair_counts, reversed_cache)
        # update, add new pretoken contrbution
        pair_counts, reversed_cache = _add_new_contribution(new_pretoken, pair_counts, reversed_cache)

    
    return pair_counts, reversed_cache

# NEED
def _pick_best_mergetoken(pair_count: dict[tuple[bytes], int]) -> tuple[tuple[bytes], int]:
        try:
            return max(
                pair_count.items(),
                key = lambda kv: (kv[1], kv[0])
            )
        except Exception as e:

        # Log or print the freqs that caused the failure
            print("Error picking best token, pair_count was:", pair_count)
            raise


# NEED
def train_bpe(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    # Init vocab
    vocab: dict[int, bytes] = init_vocab(special_tokens)
    # Init merges
    merges: list[tuple[bytes, bytes]] = []

    # Read training data
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Removing special tokens and pre-tokenization
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)

    # Build the first pair count and cache(pair to corresponding pretokens)
    pair_counts, reversed_cache = build_paircount_and_cache(pretokens)

    for i in range(vocab_size - 256 - len(special_tokens)):
        # Pick best adjcent tokens to merge
        best_pair = _pick_best_mergetoken(pair_counts)

        # Log pair counts, best pair and step
        dump_pair_count(pair_counts, best_pair, i)

        # Update pair counts and cache
        pair_counts,  reversed_cache = merge_new(pair_counts, reversed_cache, best_pair[0])

        # TODO: optimize point, insert vocab and merges two times
        # Update vocabs
        update_vocab(vocab, best_pair)
        # Update merges
        merges.append((best_pair[0][0], best_pair[0][1]))
    
    return vocab, merges


# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 500, ["<|endoftext|>"])
# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 263, ["<|endoftext|>"])

# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 320, ["<|endoftext|>"])

# print("vocab:", vocab)
# print("merges:", merges)