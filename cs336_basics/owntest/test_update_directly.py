import pytest

from cs336_basics.train_bpe import pair_counts_context
from cs336_basics.train_bpe import consutrct_new_pair
from cs336_basics.train_bpe import update_directly


@pytest.mark.parametrize("pattern, expected", [
    # test-case 1
    (
        (
            (b's', b'l'),
            b'lo',  
            1, # type 1
        ),
        (b's', b'lo'),
    ),
    # test-case 2
    (
        (
            (b'o', b'e'),
            b'lo',  
            2, # type 1
        ),
        (b'lo', b'e'),
    ),
])
def test_consutrct_new_pair_param(pattern, expected):
    assert consutrct_new_pair(*pattern) == expected


@pytest.mark.parametrize("pattern, expected", [
    # test-case 1
    (
        (
            pair_counts_context(
                merged_token_pair_count = ((b'l', b'o'), 18),
                merged_token_combined = b'lo',
                involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
                involved_paircount_type2 = [((b'o', b'e'), 10)],
                type1_directly = True,
                type2_directly = False,
                new_pair_count = {(b'l', b'e'): 10},
                last_pair_changed_count = 18,
            ),
            1,  # type 1
        ),

        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = True,
            type2_directly = False,
            new_pair_count = {(b'l', b'e'): 10, (b's', b'lo'): 9, (b'd', b'lo'): 9},
            last_pair_changed_count = 0,
        ),
    ),
    # test-case 2
    (
        (
            pair_counts_context(
                merged_token_pair_count = ((b'l', b'o'), 18),
                merged_token_combined = b'lo',
                involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
                involved_paircount_type2 = [((b'o', b'e'), 10)],
                type1_directly = False,
                type2_directly = True,
                new_pair_count = {(b'l', b'e'): 10},
                last_pair_changed_count = 18,
            ),
            2,  # type 2
        ),

        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = False,
            type2_directly = True,
            new_pair_count = {(b'l', b'e'): 10, (b'lo', b'e'): 10},
            last_pair_changed_count = 8,
        ),
    ),
    # test-case 3
    (
        (
            pair_counts_context(
                merged_token_pair_count = ((b'l', b'o'), 18),
                merged_token_combined = b'lo',
                involved_paircount_type1 = [((b's', b'l'), 4), ((b'd', b'l'), 3), ((b't', b'o'), 2)],
                involved_paircount_type2 = [((b'o', b'e'), 10)],
                type1_directly = True,
                type2_directly = False,
                new_pair_count = {(b'l', b'e'): 10},
                last_pair_changed_count = 18,
            ),
            1,  # type 2
        ),

        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 4), ((b'd', b'l'), 3), ((b't', b'o'), 2)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = True,
            type2_directly = False,
            new_pair_count = {(b'l', b'e'): 10, (b's', b'lo'): 4, (b'd', b'lo'): 3, (b't', b'lo'): 2},
            last_pair_changed_count = 9,
        ),
    ),
])
def test_update_directly_param(pattern, expected):
    assert update_directly(*pattern) == expected


