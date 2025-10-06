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
def smoketest_vocab_merge_with_special_tokens():
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
        11: b"<|endoftext|>"
    }

    merge_list = [(b"t", b"h"), (b" ", b"c"), (b" ", "a"), (b"th", b"e"), (b" a", b"t")]

    return vocab_table, merge_list


@pytest.fixture
def smoketest_corpus():
    corpus = "the cat ate"

    return corpus

@pytest.fixture
def smoketest_corpus_with_specialtokens():
    corpus = "the cat ate<|endoftext|>the cat ate"

    return corpus

@pytest.fixture
def smoketest_tokenids():
    token_ids = [9, 7, 1, 5, 10, 3]

    return token_ids


def test_encode(smoketest_vocab_merge, smoketest_corpus):
    vocab, merge = smoketest_vocab_merge
    corpus = smoketest_corpus

    tokenizer = Tokenizer(vocab, merge)
    tokenid_list = tokenizer.encode(corpus)

    assert tokenid_list == [9, 7, 1, 5, 10, 3]

def test_encode_with_special_tokens(smoketest_vocab_merge_with_special_tokens, smoketest_corpus_with_specialtokens):
    vocab, merge = smoketest_vocab_merge_with_special_tokens
    corpus = smoketest_corpus_with_specialtokens

    tokenizer = Tokenizer(vocab, merge, ["<|endoftext|>"])
    tokenid_list = tokenizer.encode(corpus)

    assert tokenid_list == [9, 7, 1, 5, 10, 3, 11, 9, 7, 1, 5, 10, 3]


def test_pretoken(smoketest_corpus):
    right_version = [[b"t", b"h", b"e"], [b" c", b"a", b"t"], [b" a", b"t", b"e"]]

    pretokens = Tokenizer.pretokenize(smoketest_corpus, True)

    assert pretokens == right_version

def test_decode(smoketest_vocab_merge, smoketest_tokenids):
    vocab, merge = smoketest_vocab_merge
    token_ids = smoketest_tokenids

    tokenizer = Tokenizer(vocab, merge)
    text = tokenizer.decode(token_ids)

    assert text == "the cat ate"
