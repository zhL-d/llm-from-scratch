import pytest

from cs336_basics.train_bpe import pair_counts_context

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

@pytest.mark.parametrize("paircount_ctx, change_count, preserved_count, pair_index, typ,"
                         "expected_last_pair_changed_count, expected_new_pair_count", [
                             # test-case 1
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
                                3, 6, 0, 1,
                                15, {(b'l', b'e'): 10, (b's', b'l'): 6, (b's', b'lo'): 3}
                             ),
                             # test-case 2
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
                                5, 4, 1, 1,
                                13, {(b'l', b'e'): 10, (b'd', b'l'): 4, (b'd', b'lo'): 5}
                             ),
                         ])
def test_update_paircount_item(paircount_ctx, change_count, preserved_count, pair_index, typ, 
                               expected_last_pair_changed_count, expected_new_pair_count):
    
    pair_counts_ctx = paircount_ctx

    pair_counts_ctx.update_paircount_item(change_count, preserved_count, pair_index, typ)

    assert pair_counts_ctx.last_pair_changed_count == expected_last_pair_changed_count

    assert pair_counts_ctx.new_pair_count == expected_new_pair_count





@pytest.mark.parametrize("paircount_ctx, typ, pretoken, half_updated,"
                         "expected_new_pair_count", [
                             # test-case 1
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
                                1, 
                                {
                                    (b's', b'l', b'o'): 3,
                                    (b's', b'l', b'e'): 6,
                                    (b'l', b'o', b'e'): 10,
                                    (b'd', b'l', b'o'): 5,
                                    (b'd', b'l', b'e'): 4,
                                }, 
                                False,
                                {(b'l', b'e'): 10, (b's', b'l'): 6, (b's', b'lo'): 3, (b'd', b'l'): 4, (b'd', b'lo'): 5}
                             ),
                             # test-case 2
                                                          (
                                pair_counts_context(
                                    merged_token_pair_count = ((b'l', b'o'), 18),
                                    merged_token_combined = b'lo',
                                    involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9), ((b'e', b'l'), 2)],
                                    involved_paircount_type2 = [((b'o', b'e'), 10)],
                                    type1_directly = False,
                                    type2_directly = True,
                                    new_pair_count = {(b'l', b'e'): 12},
                                    last_pair_changed_count = 18,
                                ),
                                1, 
                                {
                                    (b's', b'l', b'o'): 3,
                                    (b's', b'l', b'e'): 6,
                                    (b'l', b'o', b'e'): 10,
                                    (b'd', b'l', b'o'): 5,
                                    (b'd', b'l', b'e'): 4,
                                    (b'e', b'l', b'e'): 2,
                                }, 
                                False,
                                {(b'l', b'e'): 12, (b's', b'l'): 6, (b's', b'lo'): 3, (b'd', b'l'): 4, (b'd', b'lo'): 5, (b'e', b'l'): 2}
                             ),
                            # test-case 3 - half updated
                            (
                                pair_counts_context(
                                    merged_token_pair_count = ((b'l', b'o'), 18),
                                    merged_token_combined = b'lo',
                                    involved_paircount_type1 = [((b's', b'l'), 9), ((b'd', b'l'), 9), ((b'e', b'l'), 2)],
                                    involved_paircount_type2 = [((b'o', b'e'), 10)],
                                    type1_directly = False,
                                    type2_directly = True,
                                    new_pair_count = {(b'l', b'e'): 12},
                                    last_pair_changed_count = 8,
                                ),
                                1, 
                                {
                                    (b's', b'l', b'o'): 3,
                                    (b's', b'l', b'e'): 6,
                                    (b'l', b'o', b'e'): 10,
                                    (b'd', b'l', b'o'): 5,
                                    (b'd', b'l', b'e'): 4,
                                    (b'e', b'l', b'e'): 2,
                                }, 
                                True,
                                {(b'l', b'e'): 12, (b's', b'l'): 6, (b's', b'lo'): 3, (b'd', b'l'): 4, (b'd', b'lo'): 5, (b'e', b'l'): 2}
                             ),
                         ])
def test_update_bysearch(paircount_ctx, typ, pretoken, half_updated, 
                               expected_new_pair_count):
    
    pair_counts_ctx = paircount_ctx

    pair_counts_ctx.update_bysearch(typ, pretoken, half_updated)

    assert pair_counts_ctx.new_pair_count == expected_new_pair_count

