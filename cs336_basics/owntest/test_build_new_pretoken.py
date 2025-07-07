import pytest

from cs336_basics.train_bpe import _build_new_pretoken


@pytest.mark.parametrize("old_pretoken, best_pair,"
                         "expected_new_pretoken", [
                             # test-case 1
                             (
                                (
                                    (b's', b'l', b'o'), 3,
                                ),
                                (
                                    (b'l', b'o'), 18,
                                ),
                                (
                                    (b's', b'lo'), 3,
                                ),
                             ),
                              # test-case 2
                           
                         ])
def test_build_new_pretoken(old_pretoken, best_pair,
                               expected_new_pretoken):
    
    new_pretoken = _build_new_pretoken(old_pretoken, best_pair)

    assert new_pretoken == expected_new_pretoken


