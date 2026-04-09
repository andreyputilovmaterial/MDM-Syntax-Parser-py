

class MetadataParserError(Exception):
    """Exception class for parsing errors"""
    def __init__(self, message):
        super().__init__(message) # Initialize the base exception class
        self.message = message

