import pytest

from cs336_basics.train_bpe import construct_flatpair

@pytest.fixture
def sample_flat_pair():
    return [
        (b'lo', b't'),
        (b's', b'lo'),
        (b'd', b'l', b'e'),
    ]

def test_construct_flatpair(sample_flat_pair):
    expected = [
        (b'l', b'o', b't'),
        (b's', b'l', b'o'),
        (b'd', b'l', b'e'),
    ]

    results = [construct_flatpair(pair) for pair in sample_flat_pair]

    assert results == expected