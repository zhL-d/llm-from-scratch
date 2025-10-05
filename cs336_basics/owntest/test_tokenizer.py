import pytest
from cs336_basics.tokenizer import Tokenizer


@pytest.fixture
def smoketest_vocab_merge():
    vocab_table = {
        0: b" ",
        1: b"a",
        2: b"c",
        3: b"e",
        4: b"h",
        5: b"t",
        6: b"th",
        7: b" c",
        8: b" a",
        9: b"the",
        10: b" at",
    }

    merge_list = [(b"t", b"h"), (b" ", b"c"), (b" ", "a"), (b"th", b"e"), (b" a", b"t")]

    return vocab_table, merge_list


@pytest.fixture
def smoketest_corpus():
    corpus = "the cat ate"

    return corpus


def test_encode(smoketest_vocab_merge, smoketest_corpus):
    vocab, merge = smoketest_vocab_merge
    corpus = smoketest_corpus

    tokenizer = Tokenizer(vocab, merge)
    tokenid_list = tokenizer.encode(corpus)

    assert tokenid_list == [9, 7, 1, 5, 10, 3]


def test_pretoken(smoketest_corpus):
    right_version = [[b"t", b"h", b"e"], [b" c", b"a", b"t"], [b" a", b"t", b"e"]]

    pretokens = Tokenizer.pretokenize(smoketest_corpus, True)

    assert pretokens == right_version
