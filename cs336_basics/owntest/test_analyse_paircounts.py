import pytest

from cs336_basics.train_bpe import pair_counts_context


@pytest.fixture
def sample_pretoken():
    return {
        (b's', b'l', b'o'): 3,
        (b's', b'l', b'e'): 6,
        (b'l', b'o', b'e'): 10,
        (b'd', b'l', b'o'): 5,
        (b'd', b'l', b'e'): 4,
    }

@pytest.mark.parametrize("pattern, expected", [
    (
        # test-case #1
        {
            (b's', b'l', b'o'): 3,
            (b's', b'l', b'e'): 6,
            (b'l', b'o', b'e'): 10,
            (b'd', b'l', b'o'): 5,
            (b'd', b'l', b'e'): 4,
        },
        pair_counts_context(
            merged_token_pair_count = ((b'l', b'o'), 18),
            merged_token_combined = b'lo',
            involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
            involved_paircount_type2 = [((b'o', b'e'), 10)],
            type1_directly = False,
            type2_directly = True,
            new_pair_count = {((b'l', b'e'), 10)},
            last_pair_changed_count = 18,
        )
    ),
])
def test_analyse_paircounts_param(pattern, expected, sample_pretoken):
    assert analyse_paircounts(*pattern, sample_pretoken) == expected


