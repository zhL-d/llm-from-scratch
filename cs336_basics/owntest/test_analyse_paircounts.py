import pytest

from cs336_basics.train_bpe import pair_counts_context
from cs336_basics.train_bpe import analyse_paircounts


@pytest.mark.parametrize("pattern, expected", [
    (
        # test-case #1
        {
            (b'l', b'o'): 18,
            (b's', b'l'): 9,
            (b'l', b'e'): 10,
            (b'o', b'e'): 10,
            (b'd', b'l'): 9,
        },
        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = False,
            type2_directly = True,
            new_pair_count = {(b'l', b'e'): 10},
            last_pair_changed_count = 18,
        )
    ),
    (
        # test-case #2
        {
            (b'l', b'o'): 18,
            (b's', b'l'): 9,
            (b'l', b'e'): 12,
            (b'o', b'e'): 10,
            (b'd', b'l'): 9,
            (b'e', b'l'): 2,
        },
        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9), ((b'e', b'l'), 2)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = False,
            type2_directly = True,
            new_pair_count = {(b'l', b'e'): 12},
            last_pair_changed_count = 18,
        )
    ),
])
def test_analyse_paircounts_param(pattern, expected):
    assert analyse_paircounts(pattern) == expected


