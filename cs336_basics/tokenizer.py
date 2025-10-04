import regex as re


PAT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
PAT = re.compile(PAT_PATTERN)


class Tokenizer:
    def __init__(self, vocab, merges, special_tokens=None):
        """Construct a tokenizer from a given vocabulary, list of merges, and (optionally) a list of special tokens.

        Args:
            vocab: dict[int, bytes]:

            merges: list[tuple[bytes, bytes]]

            special_tokens: list[str] | None = None
        """
        pass

    def encode(self, text: str) -> list[int]:
        """
        Encode an input text into a sequence of token IDs.
        """

    @staticmethod
    def pretokenize(text: str, is_gpt: bool = True) -> list[list[bytes]]:
        """Pre-tokenize the corpus and represent each pre-token as a list of UTF-8 bytes

        Args:
            text: Corpus used for tokenization
            is_gpt: Whether use gpt pattern to pretokenize corpus

        Returns:
            List of pretokens
        """
        pretokens: list[list[bytes]] = []

        if is_gpt:
            for pretoken in PAT.finditer(text):
                pretoken_str = pretoken.group(0)
                pretoken_bytes = pretoken_str.encode("utf-8")

                pretoken_byteslist: list[bytes] = []

                if len(pretoken_bytes) > 1 and pretoken_bytes[0] == 0x20:
                    pretoken_byteslist.append(pretoken_bytes[:2])
                    pretoken_byteslist.extend([bytes([pretoken_byte]) for pretoken_byte in pretoken_bytes[2:]])
                else:
                    pretoken_byteslist = [bytes([pretoken_byte]) for pretoken_byte in pretoken_bytes]

                pretokens.append(pretoken_byteslist)
        else:
            pass

        return pretokens
