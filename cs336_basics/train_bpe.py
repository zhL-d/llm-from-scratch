import regex as re
from dataclasses import dataclass, field
import json, logging
from collections import defaultdict

logging.basicConfig(filename="/workspaces/stf-assignment1-basics/cs336_basics/feature_pair.log", filemode="w", level=logging.INFO, format="%(message)s")

import json, logging

_prev_counts = None

def _repr_pair(pair: tuple[bytes, ...]) -> str:
    # e.g. turns (b't',b'h') into "('t','h')"
    return "(" + ",".join(f"'{b.decode('utf-8', 'replace')}'" for b in pair) + ")"

def dump_delta(pair_counts: dict[tuple[bytes,bytes],int],
               merged_token: tuple[tuple[bytes,bytes],int],
               step: int):
    global _prev_counts
    old = _prev_counts or {}
    added, removed, changed = {}, {}, {}

    # detect additions & changes
    for k, v in pair_counts.items():
        if k not in old:
            added[_repr_pair(k)] = v
        elif old[k] != v:
            changed[_repr_pair(k)] = {"old": old[k], "new": v}

    # detect removals
    for k, v in old.items():
        if k not in pair_counts:
            removed[_repr_pair(k)] = v

    # stringify merged_token
    merged_pair, merged_count = merged_token
    merged_repr = {
        "pair": _repr_pair(merged_pair),
        "count": merged_count
    }

    record = {
        "step":   step,
        "merged": merged_repr,
        "added":    added,
        "removed":  removed,
        "changed":  changed,
    }

    logging.info(json.dumps(record, ensure_ascii=False, sort_keys=True))
    _prev_counts = pair_counts.copy()



def dump_pair_count(pair_count: dict[tuple[bytes], int], merged_token: tuple[tuple[bytes], int], index: int):
    serial = { str(k): v for k, v in pair_count.items() }
    serial_merged_token = {str(merged_token[0]): merged_token[1]}
    logging.info(json.dumps({"step": index, "pair": serial, "merged": serial_merged_token}, ensure_ascii=False, sort_keys=True))


def constuct_paircount_with_cache(
        pretokens: dict[tuple[bytes], int]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], dict[tuple[bytes, ...], int]]]:
    
    pair_count: dict[tuple[bytes], int] = {}
    pc_loc_cache:  dict[tuple[bytes, ...], dict[tuple[bytes, ...], int]] = {}

    for k, v in pretokens.items():
        for i in range(len(k)-1):
            pair = k[i : i+2]
            pair_count[pair] = pair_count.get(pair, 0) + v

            inner = pc_loc_cache.setdefault(pair, {})
            inner[k] = v
    return pair_count, pc_loc_cache

@dataclass
class pair_counts_context:
    merged_token_pair_count: tuple[tuple[bytes, ...], int] = ()
    merged_token_combined: bytes = b''
    involved_paircount_type1: list[tuple[tuple[bytes, ...], int]] = field(default_factory=list)
    involved_paircount_type2: list[tuple[tuple[bytes, ...], int]] = field(default_factory=list)
    type1_directly: bool = True    # if there is no merged_token[0] in all pair[0]
    type2_directly: bool = True    # if there is no merged_token[1] in all pair[1]
    new_pair_count: dict[tuple[bytes, ...], int] = field(default_factory=dict)
    last_pair_changed_count: int = 0

    def update_paircount_item(self, change_count: int, preserved_count: int, pair_index: int, typ: int):
        if not typ == 1 and not typ == 2:
            raise ValueError("type must be 1 or 2")
        
        self.last_pair_changed_count =  self.last_pair_changed_count - change_count

        if typ == 1:
            involved_paircount = self.involved_paircount_type1
            new_pair = consutrct_new_pair(involved_paircount[pair_index][0], self.merged_token_combined, typ)
        else:
            involved_paircount = self.involved_paircount_type2
            new_pair = consutrct_new_pair(involved_paircount[pair_index][0], self.merged_token_combined, typ)


        if preserved_count != 0:
            self.new_pair_count[involved_paircount[pair_index][0]] = preserved_count
        
        if change_count != 0:
            self.new_pair_count[new_pair] = change_count

    def update_bysearch(self, typ: int, pretoken: dict[tuple[bytes, ...], int], half_updated: bool):

        if not typ == 1 and not typ == 2:
            raise ValueError("type must be 1 or 2")
        
        if typ == 1:
            involved_paircount = self.involved_paircount_type1
        else:
            involved_paircount = self.involved_paircount_type2

        if half_updated:           

            for i, paircount in enumerate(involved_paircount[:len(involved_paircount)-1]):
                change_count, preserved_count =  determine_count(typ, paircount, self.merged_token_pair_count[0], pretoken)
                self.update_paircount_item(change_count, preserved_count, i, typ)
            
            # update last pair
            last_pc_p = involved_paircount[-1][0]
            last_pc_c = involved_paircount[-1][1]

            if self.last_pair_changed_count > 0:
                last_new_pair = consutrct_new_pair(last_pc_p, self.merged_token_combined, typ)
                self.new_pair_count[last_new_pair] = self.last_pair_changed_count
            
            self.new_pair_count[last_pc_p] = last_pc_c - self.last_pair_changed_count

        else:
            for i, paircount in enumerate(involved_paircount):
                change_count, preserved_count =  determine_count(typ, paircount, self.merged_token_pair_count[0], pretoken)
                self.update_paircount_item(change_count, preserved_count, i, typ)

    def update_bysearch_no_half(self, typ: int, pretoken: dict[tuple[bytes, ...], int]):

        if not typ == 1 and not typ == 2:
            raise ValueError("type must be 1 or 2")
        
        if typ == 1:
            involved_paircount = self.involved_paircount_type1
        else:
            involved_paircount = self.involved_paircount_type2

        # if half_updated:           

        #     for i, paircount in enumerate(involved_paircount[:len(involved_paircount)-1]):
        #         change_count, preserved_count =  determine_count(typ, paircount, self.merged_token_pair_count[0], pretoken)
        #         self.update_paircount_item(change_count, preserved_count, i, typ)
            
        #     # update last pair
        #     last_pc_p = involved_paircount[-1][0]
        #     last_pc_c = involved_paircount[-1][1]

        #     if self.last_pair_changed_count > 0:
        #         last_new_pair = consutrct_new_pair(last_pc_p, self.merged_token_combined, typ)
        #         self.new_pair_count[last_new_pair] = self.last_pair_changed_count
            
        #     self.new_pair_count[last_pc_p] = last_pc_c - self.last_pair_changed_count

        # else:
        for i, paircount in enumerate(involved_paircount):
            change_count, preserved_count =  determine_count(typ, paircount, self.merged_token_pair_count[0], pretoken)
            self.update_paircount_item(change_count, preserved_count, i, typ)

        


def analyse_paircounts(pair_counts: dict[tuple[bytes, ...], int]) -> pair_counts_context:
    # first round analysis
    pcc = pair_counts_context()
    #TODO: O(n)?
    pcc.merged_token_pair_count =  max(
        pair_counts.items(),
        key = lambda kv: (kv[1], kv[0]),
    )
    pcc.merged_token_combined = pcc.merged_token_pair_count[0][0] + pcc.merged_token_pair_count[0][1]
    pcc.last_pair_changed_count = pcc.merged_token_pair_count[1]
    del(pair_counts[pcc.merged_token_pair_count[0]])

    # pcc.involved_paircount_type1 = []
    # pcc.involved_paircount_type2 = []

    # pcc.type1_directly = True
    # pcc.type2_directly = True

    # pcc.new_pair_count = {}

    # second round analysis
    merged_token_pair = pcc.merged_token_pair_count[0]
    for pair, count in pair_counts.items():
        if merged_token_pair[0] == pair[1]:
            pcc.involved_paircount_type1.append((pair, count))
        elif merged_token_pair[1] == pair[0]:
            pcc.involved_paircount_type2.append((pair, count))
        else:
            if merged_token_pair[0] == pair[0]:
                pcc.type1_directly = False
            if merged_token_pair[1] == pair[1]:
                pcc.type2_directly = False

            pcc.new_pair_count[pair] = count
    
    return pcc
            
    

def construct_pair_search_pattern(typ: int, pair: tuple[bytes, ...], merged_token_pair: tuple[bytes, ...]) -> tuple[bytes, ...]:
    if not typ == 1 and not typ == 2:
        raise ValueError("type must be 1 or 2")
    if typ == 1:
        return pair + (merged_token_pair[1],)
    else:
        return (merged_token_pair[0],) + pair

def construct_flatpair(pair: tuple[bytes, ...]) -> tuple[bytes, ...]:
    # import pdb; pdb.set_trace()

    flat_pair: tuple[bytes, ...] = ()

    for part in pair:
        if len(part) > 1:
            for i in range(len(part)):
                flat_pair = flat_pair + (part[i:i+1],)  # Extract single byte
        else:
            flat_pair = flat_pair + (part,)
    
    return flat_pair

# def count_occurrences(pair: tuple[bytes, ...], pretoken: dict[tuple[bytes, ...], int]) -> int:
#     flat_pair = construct_flatpair(pair)

#     count_overall = 0
#     len_flat_pair = len(flat_pair)

#     for pretoken_pair, pretoken_count in pretoken.items():
#         count = 0
#         for i in range(len(pretoken_pair) - len_flat_pair + 1):
#             if pretoken_pair[i:i+len_flat_pair] == flat_pair:
#                 count = count + 1
        
#         count_overall = count_overall + count * pretoken_count
    
#     return count_overall

# #return: changed_count, new_loc_pretoken_cache_item, keep

# def analyse_cache_item(
#         loc_pretoken_cache_item: tuple[tuple[bytes, ...], int],
#         pair: tuple[bytes, ...], 
#         merged_token_pair: tuple[bytes, ...],
#         typ: int
#         ) -> tuple[int, dict[tuple[bytes, ...], int], bool]:

#     count_overall = 0
#     keep: bool = 0
#     count = 0

#     pretoken_pair = loc_pretoken_cache_item[0]
#     pretoken_count = loc_pretoken_cache_item[0]

#     new_pretoken_pair: tuple[bytes, ...] = ()

#     i = 0
#     j = i + 1

#     search_pattern = pair

#     while i < len(pretoken_pair) - 1:
#         if pretoken_pair[i : i+2] == search_pattern:
#             if i+2 >= len(pretoken_pair):
#                 new_pretoken_pair = new_pretoken_pair + pretoken_pair[i : i+2]
#                 i =  i + 1
#             elif pretoken_pair[i+2] == merged_token_pair[1]:
#                 merged_token = (merged_token_pair[0] + merged_token_pair[1],)
#                 new_pretoken_pair = new_pretoken_pair + pretoken_pair[i] + merged_token
#             else:
#                 keep = True
#                 new_pretoken_pair = new_pretoken_pair + pretoken_pair[i : i+3]
#         else:
#             new_pretoken_pair = new_pretoken_pair + pretoken_pair[i : i+2]


#     while j < len(pretoken_pair):
#         if not keep:
#             search_pattern = pair
#             if pretoken_pair[i : i+2] == pair:

#         if not keep and pretoken_pair[i : i+2] == pair:
#             if i[i+2] == merged_token[1]:
#                 # TODO: construct new pair add new pretoken
#                 count = count + 1
#             else:
# #                 keep = True
# #                 # TODO: change to compare whole search pattern



#     for i in range(len(pretoken_pair) -  + 1):
#         if pretoken_pair[i:i+pretoken_pair] == merged_token:
#             count = count + 1
        
#         count_overall = count_overall + count * pretoken_count
    
#     # find sl in pretokken item, if have, flag sl, if it's essentially slo, flag false sl, at same time construct new pretoken
#     # once find sl, then start to find slo
#     # pretoken should only have one copy
#     return count_overall


def count_occurrences_using_cache(
        pretoken: dict[tuple[bytes, ...], int],
        pair: tuple[bytes, ...], 
        search_pattern: tuple[bytes, ...], 
        cache: dict[tuple[bytes, ...], dict[tuple[bytes, ...], int]]
        ) -> tuple[int, dict[tuple[bytes, ...], dict[tuple[bytes, ...], int]]]:
     
    
    flat_pair = construct_flatpair(flat_pair)

    count_overall = 0
    len_flat_pair = len(flat_pair)

    for pretoken_pair, pretoken_count in pretoken.items():
        count = 0
        for i in range(len(pretoken_pair) - len_flat_pair + 1):
            if pretoken_pair[i:i+len_flat_pair] == flat_pair:
                count = count + 1
        
        count_overall = count_overall + count * pretoken_count
    
    return count_overall

def determine_count(
        typ: int, 
        pair_count: tuple[tuple[bytes, ...], int], 
        merged_token_pair: tuple[bytes, ...], 
        pretoken: dict[tuple[bytes, ...], int]) -> tuple[int, int]:
    
    if not typ == 1 and not typ == 2:
        raise ValueError("type must be 1 or 2")
    
    search_pattern = construct_pair_search_pattern(typ, pair_count[0], merged_token_pair)

    # change_count = count_occurrences(search_pattern, pretoken)
    change_count = 0
    return change_count, pair_count[1] - change_count

def determine_count_using_cache(
        typ: int, 
        pair_count: tuple[tuple[bytes, ...], int],
        cache: dict[tuple[bytes, ...], dict[tuple[bytes, ...], int]],
        merged_token_pair: tuple[bytes, ...], 
        pretoken: dict[tuple[bytes, ...], int]) -> tuple[int, int]:
    
    if not typ == 1 and not typ == 2:
        raise ValueError("type must be 1 or 2")
    
    search_pattern = construct_pair_search_pattern(typ, pair_count[0], merged_token_pair)

    change_count = count_occurrences_using_cache(pair_count[0], search_pattern, cache)
    return change_count, pair_count[1] - change_count

def consutrct_new_pair(pair: tuple[bytes, ...], merged_token_combined: bytes, typ: int) -> tuple[bytes, ...]:
    if not typ == 1 and not typ == 2:
        raise ValueError("type must be 1 or 2")
    
    if typ == 1:
        return pair[0], merged_token_combined
    else:
        return merged_token_combined, pair[1]

def update_directly(paircount_ctx: pair_counts_context, typ: int) -> pair_counts_context:
    if not typ == 1 and not typ == 2:
        raise ValueError("type must be 1 or 2")
    
    merged_token_combined = paircount_ctx.merged_token_combined
    
    if typ == 1:
        for paircount in paircount_ctx.involved_paircount_type1:
            new_pair = consutrct_new_pair(paircount[0], merged_token_combined, typ)
            paircount_ctx.new_pair_count[new_pair] = paircount[1]

            paircount_ctx.last_pair_changed_count = paircount_ctx.last_pair_changed_count - paircount[1]
        
        return paircount_ctx
    else:
        for paircount in paircount_ctx.involved_paircount_type2:
            new_pair = consutrct_new_pair(paircount[0], merged_token_combined, typ)
            paircount_ctx.new_pair_count[new_pair] = paircount[1]

            paircount_ctx.last_pair_changed_count = paircount_ctx.last_pair_changed_count - paircount[1]

        return paircount_ctx
    
def update_pair_count(
        pair_count: dict[tuple[bytes, ...], int], 
        pretoken: dict[tuple[bytes, ...], int]
        ) -> tuple[dict[tuple[bytes, ...], int], tuple[tuple[bytes, ...], int]]:

    paircount_ctx = analyse_paircounts(pair_count)

    if paircount_ctx.type1_directly and paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 1)
        paircount_ctx = update_directly(paircount_ctx, 2)

    elif paircount_ctx.type1_directly and not paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 1)
        paircount_ctx.update_bysearch(2, pretoken, True)

    elif not paircount_ctx.type1_directly and paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 2)
        paircount_ctx.update_bysearch(1, pretoken, True)

    else:

        paircount_ctx.update_bysearch(1, pretoken, False)
        paircount_ctx.update_bysearch(2, pretoken, False)

    return paircount_ctx.new_pair_count, paircount_ctx.merged_token_pair_count


def update_pair_count_nohalf(
        pair_count: dict[tuple[bytes, ...], int], 
        pretoken: dict[tuple[bytes, ...], int]
        ) -> tuple[dict[tuple[bytes, ...], int], tuple[tuple[bytes, ...], int]]:

    paircount_ctx = analyse_paircounts(pair_count)

    if paircount_ctx.type1_directly and paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 1)
        paircount_ctx = update_directly(paircount_ctx, 2)

    elif paircount_ctx.type1_directly and not paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 1)
        paircount_ctx.update_bysearch_no_half(2, pretoken)

    elif not paircount_ctx.type1_directly and paircount_ctx.type2_directly:

        paircount_ctx = update_directly(paircount_ctx, 2)
        paircount_ctx.update_bysearch_no_half(1, pretoken)

    else:

        paircount_ctx.update_bysearch_no_half(1, pretoken)
        paircount_ctx.update_bysearch_no_half(2, pretoken)

    return paircount_ctx.new_pair_count, paircount_ctx.merged_token_pair_count



    


string = """\
low low low low low
lower lower widest widest widest
newest newest newest newest newest newest
"""

def init_vocab(special_tokens : list[str]) -> dict[int, bytes]:
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

# init pretokenization
pretokens_freq : dict[tuple[bytes], int] = {}


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
            if gpt2_regex:
                # iter.match convert to string
                token_str = token.group(0)
            else:
                token_str = token
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

# here `freqs` refer to pretoken freqs
def count_mergetokens(freqs : dict[tuple[bytes], int]) -> dict[tuple[bytes], int]:
    merged_token_count : dict[tuple[bytes], int] = {}
    for k, v in freqs.items():
        for i in range(len(k)-1):
            merged_token_count[k[i : i+2]] = merged_token_count.get(k[i : i+2], 0) + v
    return merged_token_count

def merge_optim(pair_counts : dict[tuple[bytes], int], pretokens: dict[tuple[bytes], int]) -> tuple[dict[tuple[bytes], int], tuple[tuple[bytes], int]]:

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
        try:
            return max(
                freqs.items(),
                key = lambda kv: (kv[1], kv[0])
            )
        except Exception as e:
        # Log or print the freqs that caused the failure
            print("Error picking best token, freqs was:", freqs)
            raise

        # as-is
        # return max(
        #     freqs.items(),
        #     key = lambda kv: (kv[1], kv[0])
        # )
    
    def _find_count(overlap_merged: tuple[bytes], freqs: dict[tuple[bytes], int]) -> int:
        # print("$$$pretoken:", freqs)
        # print("$$$involved combination:", overlap_merged)
        count_overall = 0

        overlap_merged = tuple(
            p[b:b+1]
            for p in overlap_merged
            for b in range(len(p))
        )
        # print("$$$involved combination-flat:", overlap_merged)

        for k, v in freqs.items():
            # print("$$$comparing pretoken:", k, v)
            i = 0
            count = 0
            while i < len(k) - len(overlap_merged) + 1:
                for j in range(len(overlap_merged)):
                    if not k[i+j] == overlap_merged[j]:
                        i = i+1
                        break
                else:
                    count = count + 1
                    i = i + len(overlap_merged)
                # if k[i] == overlap_merged[0] and k[i+1] == overlap_merged[1] and k[i+2] == overlap_merged[2]:
                #     count = count + 1
                #     i = i+2
                # i = i+1
            # print("$$$compaired pretoken, pretoken_num, count:", k, v, count)
            count_overall = count_overall + count * v
        return count_overall
    
    # def _update_pair_count(
    #         pair_counts: dict[tuple[bytes], int], 
    #         pretokens: dict[tuple[bytes], int], 
    #         merged_token: tuple[tuple[bytes], int]) -> dict[tuple[bytes], int]:
        
    #     del(pair_counts[merged_token[0]])
    #     new_pair_counts : dict[tuple[bytes], int] = {}

    

    # pick best adjacent tokens to merge
    merged_token = _pick_best_mergetoken(pair_counts)

    # update pair count

    # remove best token
    # update pair counts
    # print("***update pair count***")
    del(pair_counts[merged_token[0]])
    # print("delete merged token", pair_counts)

    new_pair_counts : dict[tuple[bytes], int] = {}

    for k, v in pair_counts.items():
        # print("***check if pair need update", k, v)
        if k[1] == merged_token[0][0]:
            # find count and update pair count
            # find count for updating
            # check if pretoken item contain this combination and the times of combination
            # print("$$$need update", k[1], merged_token[0][0])
            count = _find_count((k[0], k[1], merged_token[0][1]), pretokens)
            # print("$$$count_overall:", k, count)
            if not count == 0:
                # print("$$$have combination in pretoken")
                updated_count = v - count
                # print("$$$update count:", k, updated_count)
                if not updated_count == 0:
                    new_pair_counts[k] = updated_count
                    # print("update new_pair_counts", new_pair_counts)
                
                new_pair_counts[(k[0], merged_token[0][0] + merged_token[0][1])] = count
                # print("update new_pair_counts", new_pair_counts)
            else:
                # print("$$$no combination in pretoken")
                new_pair_counts[k] = v
                # print("update new_pair_counts", new_pair_counts)
        elif k[0] == merged_token[0][1]:
            # print("$$$need update", k[0], merged_token[0][1])
            # find count and update pair count
            count = _find_count((merged_token[0][0], k[0], k[1]), pretokens)
            # print("$$$count_overall:", k, count)
            if not count == 0:
                updated_count = v - count
                # print("$$$update count:", updated_count)
                if not updated_count == 0:
                    new_pair_counts[k] = updated_count
                    # print("update new_pair_counts", new_pair_counts)            

                new_pair_counts[(merged_token[0][0] + merged_token[0][1], k[1])] = count
                # print("update new_pair_counts", new_pair_counts)
            else:
                # print("$$$no combination in pretoken")
                new_pair_counts[k] = v
                # print("update new_pair_counts", new_pair_counts)        
            
        else:
            # print("$$$no need update", k)
            new_pair_counts[k] = v
            # print("update new_pair_counts", new_pair_counts)
            
    
    # merges.append((merged_token[0][0], merged_token[0][1]))

    return new_pair_counts, merged_token

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
def train_bpe_old(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
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
        merged_token = merge(pretokens)
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
        # update pretokens
        pretokens = merge_pretoken(pretokens, merged_token)
    
    return vocab, merges

# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 263, ["<|endoftext|>"])
# train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/training_data.txt", 263, ["<|endoftext|>"])

# print("vocab:", vocab)
# print("merges:", merges)



def train_bpe_problem(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
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
    # use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    # print("pretokens:", pretokens)
    # print("#####################################")
    # pretokens = pretokenize_and_count(text)

    # construct init pair count
    pair_counts = count_mergetokens(pretokens)
    # print("pair_counts:", pair_counts)
    for i in range(vocab_size - 256 - len(special_tokens)):
        # print("pair counts:", pair_counts)

        # pick best adjcent tokens to merge
        pair_counts,  merged_token = merge_optim(pair_counts, pretokens)
        # print("merged_token", merged_token)
        # print("#####################################")
        # print("pair_counts:", pair_counts)
        # TODO: optimize point, insert vocab and merges two times
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
    
    return vocab, merges


def train_bpe_with_half(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
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
    # use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), False)
    # print("pretokens:", pretokens)
    # print("#####################################")
    # pretokens = pretokenize_and_count(text)

    # construct init pair count
    pair_counts = count_mergetokens(pretokens)
    # print("pair_counts:", pair_counts)
    for i in range(vocab_size - 256 - len(special_tokens)):
        # print("pair counts:", pair_counts)

        # pick best adjcent tokens to merge
        pair_counts,  merged_token = update_pair_count(pair_counts, pretokens)
        # print("merged_token", merged_token)
        # print("#####################################")
        # print("pair_counts:", pair_counts)
        # TODO: optimize point, insert vocab and merges two times
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
    
    return vocab, merges


def train_bpe_problem(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
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
    # use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    # print("pretokens:", pretokens)
    # print("#####################################")
    # pretokens = pretokenize_and_count(text)

    # construct init pair count
    pair_counts = count_mergetokens(pretokens)
    # print("pair_counts:", pair_counts)
    for i in range(vocab_size - 256 - len(special_tokens)):
        # print("pair counts:", pair_counts)

        # pick best adjcent tokens to merge
        pair_counts,  merged_token = merge_optim(pair_counts, pretokens)
        # print("merged_token", merged_token)
        # print("#####################################")
        # print("pair_counts:", pair_counts)
        # TODO: optimize point, insert vocab and merges two times
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
    
    return vocab, merges


def train_bpe_w(input_path: str, vocab_size :int, special_tokens: list[str]) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
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
    # use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    # print("pretokens:", pretokens)
    # print("#####################################")
    # pretokens = pretokenize_and_count(text)

    # construct init pair count
    pair_counts = count_mergetokens(pretokens)
    # print("pair_counts:", json.dumps({str(k): v for k, v in pair_counts.items()}, ensure_ascii=False))
    for i in range(vocab_size - 256 - len(special_tokens)):
        # print("pair counts:", pair_counts)

        # pick best adjcent tokens to merge
        pair_counts,  merged_token = update_pair_count_nohalf(pair_counts, pretokens)
        # print("merged_token", json.dumps([[b.decode("utf-8") for b in merged_token[0]], merged_token[1]],ensure_ascii=False))
        # print("#####################################")
        # print("pair_counts:", json.dumps({str(k): v for k, v in pair_counts.items()}, ensure_ascii=False))
        # TODO: optimize point, insert vocab and merges two times
        # update vocabs
        update_vocab(vocab, merged_token)
        # update merges
        merges.append((merged_token[0][0], merged_token[0][1]))
    
    return vocab, merges




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

def _build_new_pretoken(
        old_pretoken: tuple[tuple[bytes, ...], int], 
        # best_paircount: tuple[tuple[bytes, ...], int]
        best_paircount: tuple[bytes, ...]
        ) ->  tuple[tuple[bytes, ...], int]:
    
    new_pretoken_pair = ()
    old_pretoken_pair = old_pretoken[0]
    # best_pair = best_paircount[0]
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

    # for i in range(len(old_pretoken_pair)-1):
    #     if old_pretoken_pair[i : i+2] == best_pair:
    #         new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i] + old_pretoken_pair[i+1],)
    #     else:
    #         new_pretoken_pair = new_pretoken_pair + (old_pretoken_pair[i],)
    
    new_pretoken = (new_pretoken_pair, old_pretoken[1])
    return new_pretoken

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


def merge_new(
        pair_counts: dict[tuple[bytes], int], 
        reversed_cache: dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]],
        best_pair: tuple[bytes, ...]
        ) -> tuple[dict[tuple[bytes], int], dict[tuple[bytes, ...], set[tuple[tuple[bytes, ...], int]]]]:

    affected_pretokens = reversed_cache[best_pair].copy()

    for old_pretoken in affected_pretokens:
        new_pretoken = _build_new_pretoken(old_pretoken, best_pair)

        # update, delete old pretoken contribution
        pair_counts, reversed_cache = _delete_old_contribution(old_pretoken, pair_counts, reversed_cache)
        # update, add new pretoken contrbution
        pair_counts, reversed_cache = _add_new_contribution(new_pretoken, pair_counts, reversed_cache)

    
    return pair_counts, reversed_cache


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

        # as-is
        # return max(
        #     freqs.items(),
        #     key = lambda kv: (kv[1], kv[0])
        # )



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
    # use a regex-based pre-tokenizer
    pretokens = pretokenize_and_count(remove_special_tokens(text, special_tokens), True)
    # print("pretokens:", pretokens)
    # print("#####################################")
    # pretokens = pretokenize_and_count(text)

    # construct init pair count
    pair_counts, reversed_cache = build_paircount_and_cache(pretokens)
    # print("pair_counts:", json.dumps({str(k): v for k, v in pair_counts.items()}, ensure_ascii=False))
    for i in range(vocab_size - 256 - len(special_tokens)):
        # print("pair counts:", pair_counts)

        # pick best adjcent tokens to merge
        best_pair = _pick_best_mergetoken(pair_counts)

        if not i == 0:
            dump_pair_count(pair_counts, best_pair, i)
        else:
            dump_pair_count(pair_counts, best_pair, i)

            

        pair_counts,  reversed_cache = merge_new(pair_counts, reversed_cache, best_pair[0])

        # dump_delta(pair_counts, best_pair, )

        # print("merged_token", json.dumps([[b.decode("utf-8") for b in merged_token[0]], merged_token[1]],ensure_ascii=False))
        # print("#####################################")
        # print("pair_counts:", json.dumps({str(k): v for k, v in pair_counts.items()}, ensure_ascii=False))
        # TODO: optimize point, insert vocab and merges two times
        # update vocabs
        update_vocab(vocab, best_pair)
        # update merges
        merges.append((best_pair[0][0], best_pair[0][1]))
    
    return vocab, merges


# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 500, ["<|endoftext|>"])
# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 263, ["<|endoftext|>"])

# vocab, merges = train_bpe("/workspaces/stf-assignment1-basics/cs336_basics/train_data_small.txt", 320, ["<|endoftext|>"])

# print("vocab:", vocab)
# print("merges:", merges)