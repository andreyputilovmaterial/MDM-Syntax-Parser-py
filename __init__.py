
import sys

from .tokenizer import Tokenizer
from .parser import Parser

def parse(arg):
    # TODO:
    try:
        tokens = Tokenizer(arg).tokenize()
    except Exception as e:
        # raise Exception(f'Failed while tokenization at {e}') from e
        print(f'Failed while tokenization at {e}',file=sys.stderr)
        raise e
    try:
        parser = Parser(tokens)
        variables = parser.parse_all()
        return variables
    except Exception as e:
        # raise Exception(f'Failed while parsing at {e}') from e
        print(f'Failed while parsing at {e}',file=sys.stderr)
        raise e

