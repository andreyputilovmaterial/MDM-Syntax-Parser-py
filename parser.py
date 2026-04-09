

from .common_types import MetadataParserError


class ParserError(MetadataParserError):
    """Exception class for parsing errors"""
    def __init__(self, message):
        super().__init__(message) # Initialize the base exception class
        self.message = message



class Parser:

    TYPE_KEYWORDS = {
        "categorical",
        "text",
        "info",
        "long",
        "double",
        "date",
        "loop",
        "block",
    }


    def __init__(self, tokens):

        self.tokens = tokens
        self.pos = 0


    # =============================
    # Core helpers
    # =============================

    def peek(self):

        if self.pos >= len(self.tokens):
            return None

        return self.tokens[self.pos]


    def consume(self, expected=None):

        tok = self.peek()

        if tok is None:
            raise ParserError("Unexpected EOF")

        if expected and tok.value != expected:
            raise ParserError(f"Expected \"{expected}\", got \"{tok.value}\" at position #{tok.pos} ({tok.pos_line}:{tok.pos_column})")

        self.pos += 1
        return tok


    def match(self, value):

        tok = self.peek()

        return tok and tok.value == value


    # =============================
    # Entry point
    # =============================

    def parse_all(self):

        variables = []

        while self.peek() is not None:
            variables.append(self.parse_variable())

        return variables


    # =============================
    # Labels
    # =============================

    def parse_label(self):

        tok = self.consume()

        if tok.value == "-":
            return None

        if tok.type == "STRING":
            return tok.value

        raise ParserError("Expected label string or '-'")



    # =============================
    # Properties
    # =============================

    def parse_properties(self):

        props = {}

        self.consume("[")

        while True:

            name = self.consume().value

            self.consume("=")

            value_tok = self.consume()

            if value_tok.value == "null":
                value = None

            elif value_tok.type == "NUMBER":

                if "." in value_tok.value:
                    value = float(value_tok.value)
                else:
                    value = int(value_tok.value)

            else:
                value = value_tok.value


            props[name] = value


            if self.match("]"):
                break

            self.consume(",")


        self.consume("]")

        return props


    # =============================
    # Range expressions
    # =============================

    def parse_range(self):

        lower = None
        upper = None

        self.consume("[")

        if not self.match(".."):
            lower = self.consume().value

        self.consume("..")

        if not self.match("]"):
            upper = self.consume().value

        self.consume("]")

        return (lower, upper)



    # =============================
    # Modifiers
    # =============================

    def parse_modifiers(self):

        mods = []

        while True:

            tok = self.peek()

            if not tok or tok.type != "IDENT":
                break

            name = self.consume().value

            args = []

            if self.match("("):

                self.consume("(")

                depth = 1

                while depth > 0:

                    tok = self.consume()

                    if tok.value == "(":
                        depth += 1

                    elif tok.value == ")":
                        depth -= 1

                        if depth == 0:
                            break

                    args.append(tok.value)


            mods.append(Modifier(name, args))


        return mods



    # =============================
    # Iteration blocks/elements collection/categories
    # =============================

    def parse_iteration_block(self):

        elements = []

        self.consume("{")

        while True:

            elements.append(
                self.parse_iteration_element()
            )

            if self.match("}"):
                break

            self.consume(",")

        self.consume("}")

        return elements



    # =============================
    # Iteration elements
    # =============================

    def parse_iteration_element(self):

        name = self.consume().value

        el = IterationElement(name)

        el.label = self.parse_label()


        if self.match("["):
            el.properties = self.parse_properties()


        if self.match("{"):
            el.children = self.parse_iteration_block()


        el.modifiers = self.parse_modifiers()


        return el



    # =============================
    # Fields section
    # =============================

    def parse_fields(self):

        fields = []

        self.consume("fields")

        self.consume("(")

        while not self.match(")"):

            fields.append(
                self.parse_variable()
            )

        self.consume(")")

        return fields



    # =============================
    # Variables
    # =============================

    def parse_variable(self):

        name = self.consume().value

        var = Variable(name)


        var.label = self.parse_label()


        if self.match("["):
            var.properties = self.parse_properties()


        type_tok = self.consume()

        if type_tok.value not in self.TYPE_KEYWORDS:
            raise ParserError(
                f"Invalid type '{type_tok.value}'"
            )

        var.var_type = type_tok.value


        if self.match("["):
            var.range = self.parse_range()


        if self.match("{"):
            var.iterations = self.parse_iteration_block()


        if self.match("fields"):
            var.fields = self.parse_fields()


        var.modifiers = self.parse_modifiers()


        self.consume(";")

        return var
