import regex as re
import logging

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# )

logger = logging.getLogger(__name__)


PAT_PATTERN = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
PAT = re.compile(PAT_PATTERN)


class Tokenizer:
    def __init__(
        self, vocab: dict[int, bytes], merges: list[tuple[bytes, bytes]], special_tokens: list[str] | None = None
    ):
        """Construct a tokenizer from a given vocabulary, list of merges, and (optionally) a list of special tokens.

        Args:
            vocab: dict[int, bytes]:

            merges: list[tuple[bytes, bytes]]

            special_tokens: list[str] | None = None
        """
        self.vocab = vocab
        self.reverse_vocab = {token: id for id, token in vocab.items()}
        self.merges = merges
        self.special_tokens = special_tokens

    def encode(self, text: str) -> list[int]:
        """Encode an input text into a sequence of token IDs.

        Args:
            test: Corpus used for tokenization

        Returns:
            List of tokenid corresponding to the tokenized corpus
        """
        logger.debug(f"Starting encode: corpus={text[:50]}")

        pretokens = Tokenizer.pretokenize(text)
        token_ids: list[int] = []

        for pretoken in pretokens:
            # May include multi tokens
            tokenized_pretoken = self.tokenize(pretoken)

            logger.debug(f"Pretoken={pretoken}, Tokenized pretoken={tokenized_pretoken}")

            for token in tokenized_pretoken:
                token_id = self.reverse_vocab[token]
                
                logger.debug(f"Token={token}, Token_id={token_id}")

                token_ids.append(token_id)

        return token_ids

    @staticmethod
    def pretokenize(text: str, is_gpt: bool = True) -> list[list[bytes]]:
        """Pre-tokenize the corpus and represent each pre-token as a list of UTF-8 bytes

        Args:
            text: Corpus used for tokenization
            is_gpt: Whether use gpt pattern to pretokenize corpus

        Returns:
            List of pretokens
        """
        logger.debug(f"Starting pretokenize: text_length={len(text)}, gpt_pattern={is_gpt}")

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

        logger.debug(f"Pretokenization result: {pretokens}")
        logger.info("Pretokenization complete")

        return pretokens

    def tokenize(self, pretoken: list[bytes]) -> list[bytes]:
        """Tokenize every pretoken

        Args:
            pretoken: Single pretoken

        Returns:
            Tokenized pretoken
        """
        for merge in self.merges:
            i = 0
            while i < len(pretoken)-1:
                if pretoken[:i+2] == list(merge):
                    if len(pretoken) == 2:
                        token = pretoken[i] + pretoken[i+1]
                        pretoken = [token]
                        return pretoken
                    else:
                        token = pretoken[i] + pretoken[i+1]
                        pretoken = [token] + pretoken[i+2:]
                    i += 1
                else:
                    i += 1
        
        return pretoken
