import pytest

from cs336_basics.train_bpe import constuct_paircount_with_cache



@pytest.mark.parametrize("pretoken,"
                         "expected_new_pair_count, expected_pair_count_loc_cache", [
                             # test-case 1
                             (
                                {
                                    (b's', b'l', b'o'): 3,
                                    (b's', b'l', b'e'): 6,
                                    (b'l', b'o', b'e'): 10,
                                    (b'd', b'l', b'o'): 5,
                                    (b'd', b'l', b'e'): 4,
                                }, 
                                {
                                    (b'l', b'o'): 18, 
                                    (b's', b'l'): 9, 
                                    (b'l', b'e'): 10, 
                                    (b'o', b'e'): 10, 
                                    (b'd', b'l'): 9
                                },
                                {
                                    (b'l', b'o'): {
                                            (b's', b'l', b'o'): 3, 
                                            (b'l', b'o', b'e'): 10,
                                            (b'd', b'l', b'o'): 5,
                                        },
                                    (b's', b'l'): {
                                            (b's', b'l', b'o'): 3, 
                                            (b's', b'l', b'e'): 6,
                                        },
                                    (b'l', b'e'): {
                                            (b's', b'l', b'e'): 6, 
                                            (b'd', b'l', b'e'): 4,
                                        },
                                    (b'o', b'e'): {
                                            (b'l', b'o', b'e'): 10, 
                                        },
                                    (b'd', b'l'): {
                                            (b'd', b'l', b'o'): 5,
                                            (b'd', b'l', b'e'): 4, 
                                        },
                                },
                             ),
                             # test-case 2
                         ])
def test_constuct_paircount_with_cache(pretoken, 
                               expected_new_pair_count, expected_pair_count_loc_cache):

    pair_count, pair_count_loc_cache = constuct_paircount_with_cache(pretoken)

    assert pair_count == expected_new_pair_count

    assert pair_count_loc_cache == expected_pair_count_loc_cache    

