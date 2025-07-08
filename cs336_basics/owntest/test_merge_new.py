import pytest

from cs336_basics.train_bpe import merge_new

@pytest.mark.parametrize("pair_count, reversed_cache, best_pair,"
                         "expected_new_pair_count, expected_reversed_cache", [
                             # test-case 1
                             (
                                {
                                    (b'l', b'o'): 18,
                                    (b's', b'l'): 9,
                                    (b'l', b'e'): 10,
                                    (b'o', b'e'): 10,
                                    (b'd', b'l'): 9,
                                },
                                {
                                    (b'l', b'o'): {
                                        ((b's', b'l', b'o'), 3), 
                                        ((b'l', b'o', b'e'), 10),
                                        ((b'd', b'l', b'o'), 5),
                                        },
                                    (b's', b'l'): {
                                        ((b's', b'l', b'o'), 3), 
                                        ((b's', b'l', b'e'), 6),
                                        },
                                    (b'l', b'e'): {
                                        ((b's', b'l', b'e'), 6), 
                                        ((b'd', b'l', b'e'), 4),
                                        },
                                    (b'o', b'e'): {
                                        ((b'l', b'o', b'e'), 10), 
                                        },
                                    (b'd', b'l'): {
                                        ((b'd', b'l', b'o'), 5), 
                                        ((b'd', b'l', b'e'), 4),
                                        },
                                },
                                (b'l', b'o'),
                                {
                                    (b's', b'lo'): 3,
                                    (b's', b'l'): 6,
                                    (b'l', b'e'): 10,
                                    (b'lo', b'e'): 10,
                                    (b'd', b'l'): 4,
                                    (b'd', b'lo'): 5,
                                },
                                {
                                    (b's', b'l'): {
                                        ((b's', b'l', b'e'), 6),
                                        },
                                    (b'l', b'e'): {
                                        ((b's', b'l', b'e'), 6), 
                                        ((b'd', b'l', b'e'), 4),
                                        },
                                    (b'd', b'l'): {
                                        ((b'd', b'l', b'e'), 4),
                                        },
                                    (b's', b'lo'): {
                                        ((b's', b'lo'), 3),
                                        },
                                    (b'lo', b'e'): {
                                        ((b'lo', b'e'), 10),
                                        },
                                    (b'd', b'lo'): {
                                        ((b'd', b'lo'), 5),
                                        },
                                },
                             ),
                             # test-case 2
                         ])
def test_merge_new(pair_count, reversed_cache, best_pair,
                               expected_new_pair_count, expected_reversed_cache):

    updated_pair_count, updated_reversed_cache = merge_new(pair_count, reversed_cache, best_pair)

    assert updated_pair_count == expected_new_pair_count

    assert updated_reversed_cache == expected_reversed_cache    

