import pytest

from cs336_basics.train_bpe import update_pair_count


# @pytest.fixture
# def fresh_paircount() -> pair_counts_context:

#     return pair_counts_context(
#                 merged_token_pair_count = ((b'l', b'o'), 18),
#                 merged_token_combined = b'lo',
#                 involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9)],
#                 involved_paircount_type2 = [((b'o', b'e'), 10)],
#                 type1_directly = False,
#                 type2_directly = True,
#                 new_pair_count = {(b'l', b'e'): 10},
#                 last_pair_changed_count = 18,
#             )

@pytest.mark.parametrize("pair_count, pretoken, "
                         "expected_new_pair_count, expected_merged_token_pair", [
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
                                    (b's', b'l', b'o'): 3,
                                    (b's', b'l', b'e'): 6,
                                    (b'l', b'o', b'e'): 10,
                                    (b'd', b'l', b'o'): 5,
                                    (b'd', b'l', b'e'): 4,
                                },
                                {
                                    (b's', b'lo'): 3, 
                                    (b's', b'l'): 6, 
                                    (b'l', b'e'): 10, 
                                    (b'lo', b'e'): 10, 
                                    (b'd', b'l'): 4, 
                                    (b'd', b'lo'): 5,
                                },
                                ((b'l', b'o'), 18),
                             ),
                              # test-case 2
                             (
                                {
                                    (b'l', b'o'): 7,
                                    (b'o', b'w'): 7,
                                    (b'w', b'e'): 8,
                                    (b'e', b'r'): 2,
                                    (b'w', b'i'): 3,
                                    (b'i', b'd'): 3,
                                    (b'd', b'e'): 3,
                                    (b'e', b's'): 9,
                                    (b's', b't'): 9,
                                    (b'n', b'e'): 6,
                                    (b'e', b'w'): 6,
                                },
                                {
                                    (b'l', b'o', b'w'): 5,
                                    (b'l', b'o', b'w', b'e', b'r'): 2,
                                    (b'w', b'i', b'd', b'e', b's', b't'): 3,
                                    (b'n', b'e', b'w', b'e', b's', b't'): 6,
                                },
                                {
                                    (b'l', b'o'): 7, 
                                    (b'o', b'w'): 7, 
                                    (b'w', b'e'): 8, 
                                    (b'e', b'r'): 2, 
                                    (b'w', b'i'): 3, 
                                    (b'i', b'd'): 3,
                                    (b'd', b'e'): 3,
                                    (b'e', b'st'): 9,
                                    (b'n', b'e'): 6,
                                    (b'e', b'w'): 6,
                                },
                                ((b's', b't'), 9),
                             ),
                         ])
def test_update_pair_count(pair_count, pretoken, 
                               expected_new_pair_count, expected_merged_token_pair):
    
    updated_paircount, merged_token_pair_count = update_pair_count(pair_count, pretoken)

    assert updated_paircount == expected_new_pair_count

    assert merged_token_pair_count == expected_merged_token_pair  


