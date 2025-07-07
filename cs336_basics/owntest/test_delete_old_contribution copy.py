import pytest

from cs336_basics.train_bpe import _delete_old_contribution


@pytest.mark.parametrize("pretoken, pair_count, reversed_cache,"
                         "expected_pair_count, expected_reversed_cache", [
                             # test-case 1
                             (
                                (
                                    (b's', b'l', b'o'), 3,
                                ),
                                {
                                    (b'l', b'o'): 18, 
                                    (b's', b'l'): 9, 
                                    (b'l', b'e'): 10, 
                                    (b'o', b'e'): 10, 
                                    (b'd', b'l'): 9
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
                                {
                                    (b'l', b'o'): 15, 
                                    (b's', b'l'): 6, 
                                    (b'l', b'e'): 10, 
                                    (b'o', b'e'): 10, 
                                    (b'd', b'l'): 9
                                },
                                {
                                    (b'l', b'o'): {
                                            ((b'l', b'o', b'e'), 10),
                                            ((b'd', b'l', b'o'), 5),
                                        },
                                    (b's', b'l'): {
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
                             ),
                              # test-case 2
                           
                         ])
def test_build_new_pretoken(pretoken, pair_count, reversed_cache,
                               expected_pair_count, expected_reversed_cache):
    
    updated_pair_count, updated_reversed_cache = _delete_old_contribution(pretoken, pair_count, reversed_cache)

    assert updated_pair_count == expected_pair_count
    assert updated_reversed_cache == expected_reversed_cache


