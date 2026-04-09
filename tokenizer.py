

from .common_types import MetadataParserError


class TokenizerError(MetadataParserError):
    """Exception class for parsing errors"""
    def __init__(self, message):
        super().__init__(f'Tokenizer: {message}') # Initialize the base exception class
        self.message = f'Tokenizer: {message}'



class Token:

    def __init__(
        self,
        type_,
        value,

        pos_line,
        pos_column,
        pos,

        leading_ws="",
        leading_comments=None,
        trailing_ws="",
        trailing_comments=None,
    ):
        self.type = type_
        self.value = value

        self.pos_line = pos_line
        self.pos_column = pos_column
        self.pos = pos

        self.leading_ws = leading_ws
        self.leading_comments = leading_comments or []

        self.trailing_ws = trailing_ws
        self.trailing_comments = trailing_comments or []

    def __repr__(self):

        return (
            f"{self.type}({self.value}) "
            f"@ {self.pos_line}:{self.pos_column} "
            f"LWS={repr(self.leading_ws)} "
            f"LC={self.leading_comments} "
            f"TWS={repr(self.trailing_ws)} "
            f"TC={self.trailing_comments}"
        )


class Tokenizer:

    SYMBOLS = "{}[](),;=-/\\^.#"

    KEYWORDS = {
        "categorical",
        "text",
        "long",
        "double",
        "date",
        "loop",
        "block",
        "fields",
        "null",
        "fix",
        "nocasedata",
        "exclusive",
        "nofilter",
        "canfilter",
    }

    def __init__(self, text):

        self.text = text
        self.pos = 0
        self.len = len(text)

        self.pos_line = 1
        self.pos_column = 1


    def peek(self, n=1):
        """Look ahead of n chars without consuming them"""

        if self.pos >= self.len:
            return None

        if self.pos + n > len(self.text):
            return self.text[self.pos:]
        else:
            return self.text[self.pos:self.pos+n]


    def advance(self, n=1):

        for _ in range(n):

            if self.pos >= self.len:
                return

            if self.text[self.pos] == "\n":
                self.pos_line += 1
                self.pos_column = 1
            else:
                self.pos_column += 1

            self.pos += 1
    

    def read_while(self, condition):

        start = self.pos

        while self.peek() and condition(self.peek()):
            self.advance()

        return self.text[start:self.pos]


    def read_whitespace(self):

        return self.read_while(str.isspace)
    
    def read_comment(self):
        if self.peek(2) == "'!":
            return self.read_multiline_comment()
        else:
            return self.read_single_line_comment()


    def read_single_line_comment(self):

        start = self.pos

        while self.peek() not in ("\n", None):
            self.advance()

        return self.text[start:self.pos]


    def read_multiline_comment(self):

        start = self.pos

        self.advance()  # skip !

        while True:

            if self.peek() is None:
                raise TokenizerError("Unclosed multiline comment")

            if self.peek(2) == "!'":
                self.advance()
                break

            self.advance()

        return self.text[start:self.pos]


    def read_string(self):

        result = []
        self.advance()  # skip opening "

        while True:

            ch = self.peek()

            if ch is None:
                raise TokenizerError("Unclosed string literal")

            self.advance()

            if ch == '"':

                if self.peek() == '"':
                    result.append('"')
                    self.advance()
                else:
                    break

            else:
                result.append(ch)

        return "".join(result)


    def read_identifier(self):

        return self.read_while(
            lambda c: c.isalnum() or c == "_"
        )


    def read_number(self):

        return self.read_while(
            lambda c: c.isdigit() or c == "."
        )


    def read_trivia(self):

        ws = []
        comments = []

        while True:

            start = self.pos

            whitespace = self.read_whitespace()

            if whitespace:
                ws.append(whitespace)
                continue

            if self.peek() == "'":

                comment = self.read_comment()

                comments.append(comment)
                continue

            break

        return "".join(ws), comments


    def read_token_core(self):
        
        start_line = self.pos_line
        start_column = self.pos_column
        start_pos = self.pos
        pos_tuple = (start_line,start_column,start_pos)

        ch = self.peek()

        if ch is None:
            return None


        if ch == '"':
            return ("STRING", self.read_string(), pos_tuple)


        if ch.isdigit():
            return ("NUMBER", self.read_number(), pos_tuple)


        if ch.isalpha() or ch == "_":

            ident = self.read_identifier()

            if ident in self.KEYWORDS:
                return ("KEYWORD", ident, pos_tuple)

            return ("IDENT", ident, pos_tuple)


        if self.text.startswith("..", self.pos):

            self.advance(2)

            return ("RANGE", "..", pos_tuple)


        if ch in self.SYMBOLS:

            self.advance()

            return ("SYMBOL", ch, pos_tuple)


        raise TokenizerError(f"Unexpected character: \"{ch}\" at position #{start_pos} ({start_line}:{start_column})")


    def tokenize(self):

        tokens = []

        while True:

            leading_ws, leading_comments = self.read_trivia()

            if self.peek() is None:
                break


            token_type, token_value, pos_tuple = self.read_token_core()


            trailing_ws, trailing_comments = self.read_trivia()


            token = Token(
                token_type,
                token_value,

                pos_tuple[0],
                pos_tuple[1],
                
                leading_ws,
                leading_comments,
                trailing_ws,
                trailing_comments,
            )

            tokens.append(token)

        return tokens



