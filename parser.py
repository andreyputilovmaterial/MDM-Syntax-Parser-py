

from .common_types import MetadataParserError
from . import parser_interfaces
import sys # for error reporting - to print to sys.stderr


class ParserError(MetadataParserError):
    """Exception class for parsing errors"""
    def __init__(self, message):
        msg = f'Parsing: {message}'
        super().__init__(msg) # Initialize the base exception class
        self.message = f'Parsing: {message}'

class SyntaxError(ParserError):
    """Exception class for parsing errors"""
    def __init__(self, message, parser):
        token = parser.peek()
        msg = f"{message}; ongoing token: \"{token.value}\" at #{parser.pos} ({token.pos_line}:{token.pos_column})" if token else f"{message}; last token: <UNKNOWN>"
        super().__init__(msg) # Initialize the base exception class
        self.message = f'{message}'










class Parser:

    TYPE_KEYWORDS = {
        cls.syntax_keyword: cls for cls in parser_interfaces.list_available_classes() if cls.syntax_keyword is not None
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
            raise SyntaxError("Unexpected EOF",self)

        if expected and tok.value != expected:
            raise SyntaxError(f"Expected \"{expected}\", got \"{tok.value}\"",self)

        self.pos += 1
        return tok


    def match(self, value):
        tok = self.peek()
        return tok and tok.value == value

    def imatch(self, value):
        """Same, case-insensitive"""
        tok = self.peek()
        return tok and tok.value.lower() == value.lower()

    def read_while(self, condition):

        result = []
        while self.peek() and condition(self.peek()):
            result.append(self.consume())

        return result


    # =============================
    # Entry point
    # =============================

    def parse_all(self):

        variables = []

        while self.peek() is not None:
            variables.append(self.parse_node())

        return variables


    # =============================
    # Labels
    # =============================

    def parse_label(self, optional=False):

        tok = self.peek()

        if tok.value == "-":
            tok = self.consume()
            return None

        if tok.type == "STRING":
            tok = self.consume()
            return tok.value

        if optional:
            return None
        else:
            raise SyntaxError("Expected label string or '-'",self)



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

    def parse_modifiers(self, place_or_node_type):

        mods = []

        while True:

            tok = self.peek()

            if not tok or tok.type not in ["IDENT","KEYWORD"]:
                break
            
            ALLOWED_MODIFIER_KEYWORDS = parser_interfaces.get_allowed_modifiers(place_or_node_type)

            candidates = set([
                c.lower() for c in ALLOWED_MODIFIER_KEYWORDS
            ])
            name = None
            for mod in candidates:
                if self.imatch(mod):
                    name = self.consume().value.lower()
                    break
            if name is None:
                break
            
            cls = parser_interfaces.get_modifier_class(name)
            mod = cls(name)
            mod.parse(self)

            mods.append(mod)


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
        modifiers = self.parse_modifiers('category_list')

        el = parser_interfaces.ElementsCollection()
        el.elements = elements
        el.modifiers = modifiers
        return el



    # =============================
    # Iteration elements
    # =============================

    def parse_iteration_element(self):

        name = self.consume().value

        if name.lower() == 'use':
            name = None
            label = None
            properties = None
            el = parser_interfaces.IterationElement(name)
            el.name = name
            el.label = label
            el.properties = properties
            el.parse_sl_reference(self)
            print(f"parsing category: {el}") # TODO: debug
            return
        elif self.peek().value.lower() == 'use':
            self.consume('use')
            label = None
            properties = None
            el = parser_interfaces.IterationElement(name)
            el.name = name
            el.label = label
            el.properties = properties
            el.parse_sl_reference(self)
            print(f"parsing category: {el}") # TODO: debug
            return

        label = self.parse_label(optional=True)

        properties = None
        if self.match("["):
            properties = self.parse_properties()

        el = parser_interfaces.IterationElement(name)
        el.label = label
        el.properties = properties

        el.parse(self)
        print(f"parsing category: {el}") # TODO: debug

        return el


    # =============================
    # Page elements
    # =============================

    def parse_page_element(self):

        name = self.consume().value

        label = self.parse_label(optional=True)

        properties = None
        if self.match("["):
            properties = self.parse_properties()

        el = parser_interfaces.PageElement(name)
        el.label = label
        el.properties = properties

        el.parse(self)
        print(f"parsing page element: {el}") # TODO: debug

        return el



    # # =============================
    # # Fields section
    # # =============================

    # def parse_fields(self):

    #     fields = []

    #     self.consume("fields")

    #     self.consume("(")

    #     while not self.match(")"):

    #         fields.append(
    #             self.parse_node()
    #         )

    #     self.consume(")")

    #     return fields



    # =============================
    # Variables
    # =============================

    def parse_node(self):
        
        token = self.consume()

        if token.type != "IDENT":
            raise SyntaxError(f"Expected identifier, got {token.type} (\"{token.value}\")",self)
        name = token.value

        try:

            label = self.parse_label()

            properties = {}
            if self.match("["):
                properties = self.parse_properties()

            pre_modifiers = self.parse_modifiers('node_pre') or []

            if self.match(";") and name.strip().lower() == 'HDATA'.lower():
                cls = self.TYPE_KEYWORDS[":root"]

                var = cls(name)
                var.label = label
                var.properties = properties
                var.pre_modifiers = pre_modifiers

                var.parse(self)

                self.consume(";")

                print(f"parsing item: {var}") # TODO: debug

                return var
            
            type_tok = self.consume()

            if type_tok.value not in self.TYPE_KEYWORDS:
                raise SyntaxError(f"Error parsing {name}: Node type not known '{type_tok.value}'",self)

            var_type_keyword = type_tok.value
            cls = self.TYPE_KEYWORDS[var_type_keyword]

            var = cls(name)
            var.label = label
            var.properties = properties
            var.pre_modifiers = pre_modifiers

            var.parse(self)

            self.consume(";")

            print(f"parsing item: {var}") # TODO: debug

            return var
        
        except Exception as e:
            msg_err_failed_at = f"{SyntaxError(f'Failed when parsing {name}: {e}',self)}"
            print(msg_err_failed_at,file=sys.stderr)
            raise e


