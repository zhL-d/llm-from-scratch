# import pytest

# from cs336_basics.train_bpe import construct_flatpair
# from cs336_basics.train_bpe import count_occurrences
# from cs336_basics.train_bpe import determine_count
# from cs336_basics.train_bpe import construct_pair_search_pattern

# @pytest.fixture
# def sample_flat_pair():
#     return [
#         (b'lo', b't'),
#         (b's', b'lo'),
#         (b'd', b'l', b'e'),
#     ]

# def test_construct_flatpair(sample_flat_pair):
#     expected = [
#         (b'l', b'o', b't'),
#         (b's', b'l', b'o'),
#         (b'd', b'l', b'e'),
#     ]

#     results = [construct_flatpair(pair) for pair in sample_flat_pair]

#     assert results == expected


# @pytest.fixture
# def sample_pretoken():
#     return {
#         (b's', b'l', b'o'): 3,
#         (b's', b'l', b'e'): 6,
#         (b'l', b'o', b'e'): 10,
#         (b'd', b'l', b'o'): 5,
#         (b'd', b'l', b'e'): 4,
#     }

# @pytest.mark.parametrize("pattern, expected", [
#     ((1, (b's', b'l'), (b'l', b'o')), (b's', b'l', b'o')),
#     ((2, (b'o', b'e'), (b'l', b'o')), (b'l', b'o', b'e')),
#     ((1, (b't', b'l'), (b'l', b'o')), (b't', b'l', b'o')),
# ])
# def test_construct_pair_search_pattern_param(pattern, expected):
#     assert construct_pair_search_pattern(*pattern) == expected


# @pytest.mark.parametrize("pattern, expected", [
#     ((b's', b'lo'), 3),
#     ((b'lo', b'e'), 10),
#     ((b'd', b'lo'), 5),
# ])
# def test_count_occurrences_param(pattern, expected, sample_pretoken):
#     assert count_occurrences(pattern, sample_pretoken) == expected


# @pytest.mark.parametrize("pattern, expected", [
#     ((1, ((b's', b'l'), 9), (b'l', b'o')), (3, 6)),
#     ((1, ((b'd', b'l'), 9), (b'l', b'o')), (5, 4)),
#     ((2, ((b'o', b'e'), 10), (b'l', b'o')), (10, 0)),
# ])
# def test_determine_count_param(pattern, expected, sample_pretoken):
#     assert determine_count(*pattern, sample_pretoken) == expected



