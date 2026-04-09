

import re

from .common_types import MetadataParserError



class ParserInterfaceError(MetadataParserError):
    """Exception class for parsing errors"""
    def __init__(self, message):
        msg = f'Parsing: {message}'
        super().__init__(msg) # Initialize the base exception class
        self.message = msg

class SyntaxError(ParserInterfaceError):
    """Exception class for parsing errors"""
    def __init__(self, message, parser):
        msg = f'{message} at #{parser.pos} ({parser.pos_line}:{parser.pos_column})'
        super().__init__(msg)
        self.message = msg


def sanitize_name(name):
    if name is None:
        return name
    if not re.match(r'^\s*?\w+\s*?$',name) or re.match(r'^\s*?[0-9]\w*\s*?$',name):
        raise ParserInterfaceError(f"Improper identifier name: \"{name}\"")
    return re.sub(r'^\s*(\w*)\s*$',lambda m: m[1],name)






class Modifier:
    is_funcitonal = None
    def __init__(self, name):
        self.name = name
        self.args = None
    def __str__(self):
        return f"{self.name}"
    def parse(self,parser):
        raise NotImplementedError(f"Abstract class: Modifier; name == {self.name}")

class ModifierPlain(Modifier):
    """Derivative"""
    is_functional = False
    def parse(self,parser):
        return

class ModifierFunctional(Modifier):
    """Derivative"""
    is_functional = True
    def parse(self,parser):
        args = []

        if parser.match("("):

            parser.consume("(")
            depth = 1

            while depth > 0:

                tok = parser.consume()

                if tok.value == "(":
                    depth += 1

                elif tok.value == ")":
                    depth -= 1

                    if depth == 0:
                        break

                args.append(tok.value)
        self.args = args

class ModifierFunctionalArgNumeric(ModifierFunctional):
    """Derivative"""
    is_functional = True
    def parse(self,parser):

        parser.consume("(")

        txt = None
        if parser.match(")"):
            txt = None
        else:
            token = parser.consume()
            if token.type != "NUMBER":
                raise ParserInterfaceError(f"Parsing {self.name} modifier: param must be a number")
            txt = token.value

        parser.consume(")")

        self.args = [txt]

class ModifierFunctionalArgString(ModifierFunctional):
    """Derivative"""
    is_functional = True
    def parse(self,parser):

        parser.consume("(")

        txt = None
        if parser.match(")"):
            txt = None
        else:
            token = parser.consume()
            if token.type != "STRING":
                raise ParserInterfaceError(f"Parsing {self.name} modifier: param must be a string")
            txt = token.value

        parser.consume(")")

        self.args = [txt]

class ModifierFunctionalArgFields(ModifierFunctional):
    """Derivative"""
    is_functional = True
    def parse(self,parser):

        parser.consume("(")

        self.args = []
        while not parser.match(")"):
            self.args.append(parser.parse_node())

        parser.consume(")")





class NodeBase:
    """
    Base abstract class for all types of items defined in metadata
    """
    syntax_keyword = None
    is_data_variable = False

    def __init__(self, name):
        self.name = sanitize_name(name)
        self.label = None
        self.properties = {}
        self.notes = []
        self.var_type = None
        self.ref = None
        self.range = None
        self.elements = None
        self.fields = None
        self.helperfields = None
        self.modifiers = []
    
    def validate_modifier(self,mod):
        if mod in ['grid','expand','column'] and self.syntax_keyword != 'loop':
            return False
        if mod =='nocasedata' and not self.is_data_variable:
            return False
        return True
    
    def parse(self, parser):
        """
        Implement parsing logic here in subclasses
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement parse()")
    
    def __str__(self):
        def escape_double_quotes(s):
            s = f"{s}"
            return s.replace('"','""')
        name_part = f"{self.name}"
        label_part = f' "{escape_double_quotes(self.label)}"' if self.label is not None else " -"
        properties = [f'{prop_name} = "{escape_double_quotes(prop_value)}"' for prop_name,prop_value in (self.properties or {}).items()]
        properties_part = f"[ {', '.join(properties)} ]" if len(properties)>0 else ""
        var_type = self.__class__.syntax_keyword
        var_type_part = f" {var_type}" if var_type else ""
        ref_part = f" -> {self.ref}" if self.ref else ""
        modifier_part = "".join([f" {mod_name}" for mod_name in (self.modifiers or [])])
        return f"{name_part}{label_part}{properties_part}{var_type_part}{ref_part}{modifier_part};"


class Node(NodeBase):
    """Someting that can appear at top level"""



class NodeRoot(Node):
    """Root node"""
    syntax_keyword = ":root"
    def parse(self, parser):
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")
    def validate_modifier(self, mod):
        # return super().validate_modifier(mod)
        return False

class NodeSharedlist(Node):
    """Shared list"""
    syntax_keyword = "define"
    def parse(self, parser):
        if not parser.match("{"):
            raise SyntaxError("Expecting \"{\" in Shared List definition",parser)
        self.elements = parser.parse_iteration_block()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeInfo(Node):
    """Info node"""
    syntax_keyword = "info"
    def parse(self, parser):
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeCategorical(Node):
    """Categorical variable"""
    syntax_keyword = "categorical"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        if not parser.match("{"):
            raise SyntaxError("Expecting \"{\" in Shared List definition",parser)
        self.elements = parser.parse_iteration_block()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeText(Node):
    """Text variable"""
    syntax_keyword = "text"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeNumericInt(Node):
    """Numeric (integer) variable"""
    syntax_keyword = "long"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        self.modifiers = parser.parse_modifiers('variable')

class NodeNumericFloat(Node):
    """Numeric (intfloating-pointeger) variable"""
    syntax_keyword = "double"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeDatetime(Node):
    """Datetime variable"""
    syntax_keyword = "date"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeBoolean(Node):
    """Boolean variable"""
    syntax_keyword = "boolean"
    is_data_variable = True
    def parse(self, parser):
        if parser.match("["):
            self.range = parser.parse_range()
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeBlock(Node):
    """Block with fields"""
    syntax_keyword = "block"
    is_data_variable = False
    def parse(self, parser):
        parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['-'])
        parser.consume("fields")
        parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['-'])
        if parser.match("("):
            parser.consume("(")
            self.fields = []
            while not parser.match(")"):
                self.fields.append(parser.parse_node())
            parser.consume(")")
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodeArray(Node):
    """Grid/Loop/Array"""
    syntax_keyword = "loop"
    is_data_variable = False
    def parse(self, parser):
        if parser.match("{"):
            self.elements = parser.parse_iteration_block()
        parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['-'])
        parser.consume("fields")
        parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['-'])
        if parser.match("("):
            parser.consume("(")
            self.fields = []
            while not parser.match(")"):
                self.fields.append(parser.parse_node())
            parser.consume(")")
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")

class NodePage(Node):
    """Page"""
    syntax_keyword = "page"
    is_data_variable = False
    def parse(self, parser):
        parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['-'])
        if parser.match("("):
            parser.consume("(")
            self.fields = []
            while not parser.match(")"):
                self.fields.append(parser.parse_page_element())
                if parser.match(")"):
                    break
                parser.consume(",")
            parser.consume(")")
        self.modifiers = parser.parse_modifiers('variable')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")
    def validate_modifier(self, mod):
        # return super().validate_modifier(mod)
        return False




class IterationElement(NodeBase):
    """ aka "Category" """
    ref = None
    def parse(self,parser):
        pre_modifiers = parser.parse_modifiers('category_def') or []
        if 'use' in pre_modifiers: # TODO: clearly capture all "modifiers"
            return self.parse_sl_reference(parser)
        if parser.match('{'):
            self.elements = parser.parse_iteration_block()
        else:
            self.elements = None
        self.modifiers = parser.parse_modifiers('category')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")
    def parse_sl_reference(self,parser):
        skipped_chars = parser.read_while(lambda token: token.type=="SYMBOL" and token.value in ['\\','.','^'])
        name = parser.consume().value
        label = parser.parse_label(optional=True)
        self.ref = name
        self.modifiers = parser.parse_modifiers('category')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")
        # raise NotImplementedError('Reference to another SL: not implemented')


class ElementsCollection(NodeBase):
    """ aka set of "Categories" """
    ref = None
    def __init__(self,name=None):
        super().__init__(name)
    def parse(self,parser):
        raise NotImplementedError("ElementCollection.parse(): Can't do it, as of current design")



class PageElement(NodeBase):
    """ Page entry """
    def parse(self,parser):
        self.modifiers = parser.parse_modifiers('category')
        for mod in self.modifiers or []:
            if not self.validate_modifier(mod):
                raise ParserInterfaceError(f"Modifier {mod} is not allowed on this type of item (processing {self.name})")





KNOWN_MODIFIERS = {
    'fix': {
        'cls': ModifierPlain, 'available_at': ['category','category_list'],
    },
    'ran': {
        'cls': ModifierPlain, 'available_at': ['category_list'],
    },
    'asc': {
        'cls': ModifierPlain, 'available_at': ['category_list'],
    },
    'nofiler': {
        'cls': ModifierPlain, 'available_at': ['category','category_list'],
    },
    'canfilter': {
        'cls': ModifierPlain, 'available_at': ['category','category_list'],
    },
    'other': {
        'cls': ModifierFunctional, 'available_at': ['category'],
    },
    'exclusive': {
        'cls': ModifierPlain, 'available_at': ['category'],
    },
    'na': {
        'cls': ModifierPlain, 'available_at': ['category'],
    },
    'nocasedata': {
        'cls': ModifierPlain, 'available_at': ['variable'],
    },
    'grid': {
        'cls': ModifierPlain, 'available_at': ['variable'],
    },
    'column': {
        'cls': ModifierPlain, 'available_at': ['variable'],
    },
    'expand': {
        'cls': ModifierPlain, 'available_at': ['variable'],
    },
    'sublist': {
        'cls': ModifierPlain, 'available_at': ['category_def'],
    },
    'factor': {
        'cls': ModifierFunctionalArgNumeric, 'available_at': ['category'],
    },
    'axis': {
        'cls': ModifierFunctionalArgString, 'available_at': ['variable'],
    },
    'style': {
        'cls': ModifierFunctional, 'available_at': ['node_pre'],
    },
    'validation': {
        'cls': ModifierFunctionalArgString, 'available_at': ['variable'],
    },
    'helperfields': {
        'cls': ModifierFunctionalArgFields, 'available_at': ['variable'],
    },
    'initialanswer': {
        'cls': ModifierFunctional, 'available_at': ['variable'],
    },
    'mustanswer': {
        'mustanswer': 'initialanswer', 'cls': ModifierFunctional, 'available_at': ['variable'],
    },
}


def get_modifier_class(name):
    name = name.strip().lower()
    record = KNOWN_MODIFIERS.get(name,None)
    if record is None:
        raise ParserInterfaceError(f"Modifier not known: {name}")
    return record['cls']

def get_allowed_modifiers(place_or_node_type):
    return [key for key, value in KNOWN_MODIFIERS.items() if place_or_node_type in value['available_at']]





def __list_classes(cls):
    result = []
    for subclass in cls.__subclasses__():
        result.append(subclass)
        result.extend(__list_classes(subclass))
    return result

def list_available_classes():
    return __list_classes(Node)
