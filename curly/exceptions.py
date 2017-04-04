# -*- coding: utf-8 -*-
"""This module has a number of exceptions raises by Curly.

Please remember that all exceptions are derived from
:py:exc:`CurlyError` which is a subclass of :py:exc:`ValueError`.
"""


class CurlyError(ValueError):
    """Main exception raised from Curly."""

    def __init__(self, message, *args, **kwargs):
        super().__init__(message.format(*args, **kwargs))


class CurlyEvaluateError(CurlyError):
    """Expression evaluation error."""


class CurlyLexerError(CurlyError):
    """Errors on lexing phase."""


class CurlyParserError(CurlyError):
    """Errors on parsing phase."""


class CurlyLexerStringDoesNotMatchError(CurlyLexerError):
    """Exception raised if given string does not match regular expression."""

    def __init__(self, text, pattern):
        super().__init__("String {0!r} is not valid pattern {1!r}",
                         text, pattern.pattern)


class CurlyEvaluateNoKeyError(CurlyEvaluateError):
    """Exception raised if context has no required key."""

    def __init__(self, context, key):
        super().__init__("Context {0!r} has no key {1!r}", context, key)


class CurlyParserUnknownTokenError(CurlyParserError):
    """Exception raised on unknown token type."""

    def __init__(self, token):
        super().__init__("Unknown token {0!s}".format(token))


class CurlyParserUnknownStartBlockError(CurlyParserError):
    """Exception raised if function of start block is unknown."""

    def __init__(self, token):
        super().__init__("Unknown block tag {0} for token {1!s}",
                         token.contents["function"], token)


class CurlyParserUnknownEndBlockError(CurlyParserError):
    """Exception raised if function of end block is unknown."""

    def __init__(self, token):
        super().__init__("Unknown block tag {0} for token {1!s}",
                         token.contents["function"], token)


class CurlyParserFoundNotDoneError(CurlyParserError):
    """Exception raised if some node is not done."""

    def __init__(self, node):
        super().__init__("Cannot find enclosement statement for {0!s}",
                         node.token)


class CurlyParserNoUnfinishedNodeError(CurlyParserError):
    """Exception raised if searching for not finished node is failed."""

    def __init__(self):
        super().__init__("Cannot find not finished node.")


class CurlyParserUnexpectedUnfinishedNodeError(CurlyParserError):
    """Exception raised if we found unfinished node which is not expected."""

    def __init__(self, search_for, node):
        super().__init__("Excepted to find {0} node but found {1!s} instead",
                         search_for, node)
