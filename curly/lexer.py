# -*- coding: utf-8 -*-


import collections

from curly import utils


class Token:

    __slots__ = "contents", "raw_string"

    REGEXP = utils.make_regexp(".+")

    def __init__(self, raw_string):
        matcher = self.REGEXP.match(raw_string)
        if matcher is None:
            raise ValueError(
                "String {0!r} is not valid for pattern {1!r}".format(
                    raw_string, self.REGEXP.pattern))

        self.contents = self.extract_contents(matcher)
        self.raw_string = raw_string

    def extract_contents(self, matcher):
        return {}

    def __str__(self):
        return ("<{0.__class__.__name__}(raw={0.raw_string!r}, "
                "contents={0.contents!r})>").format(self)

    def __repr__(self):
        return str(self)


class VarTokenMixin:

    @staticmethod
    def extract_contents(matcher):
        return {"var": matcher.group(1).strip()}


class PrintToken(VarTokenMixin, Token):
    REGEXP = utils.make_regexp(
        r"""
        \{\{                          # opening {{
        ([a-zA-Z0-9_\. \t\n\r\f\v]+)  # group 1, 'var' in {{ var }}
        \}\}                          # closing }}
        """
    )


class IfStartToken(VarTokenMixin, Token):
    REGEXP = utils.make_regexp(
        r"""
        \{\?                          # opening {?
        ([a-zA-Z0-9_\. \t\n\r\f\v]+)  # group 1, 'var' in {? var ?}
        \?\}                          # closing ?}
        """
    )


class IfEndToken(Token):
    REGEXP = utils.make_regexp(r"\{\?\}")


class LoopStartToken(VarTokenMixin, Token):
    REGEXP = utils.make_regexp(
        r"""
        \{\%                          # opening {%
        ([a-zA-Z0-9_\. \t\n\r\f\v]+)  # group 1, 'var' in {% var %}
        \%\}                          # closing %}
        """
    )


class LoopEndToken(Token):
    REGEXP = utils.make_regexp(r"\{%\}")


class LiteralToken(Token):

    TEXT_UNESCAPE = utils.make_regexp(r"\\(.)")

    def __init__(self, text):
        self.raw_string = text
        self.contents = {"text": self.TEXT_UNESCAPE.sub(r"\1", text)}


TOKENS = collections.OrderedDict()
TOKENS["print"] = PrintToken
TOKENS["if_start"] = IfStartToken
TOKENS["if_end"] = IfEndToken
TOKENS["loop_start"] = LoopStartToken
TOKENS["loop_end"] = LoopEndToken

TOKENIZER_REGEXP = utils.make_regexp(
    "|".join(
        "(?P<{0}>{1})".format(k, v.REGEXP.pattern) for k, v in TOKENS.items()
     )
)


def tokenize_iter(text):
    previous_end = 0
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    for matcher in TOKENIZER_REGEXP.finditer(text):
        if matcher.start(0) != previous_end:
            yield LiteralToken(text[previous_end:matcher.start(0)])
        previous_end = matcher.end(0)

        match_groups = matcher.groupdict()
        token_class = TOKENS[matcher.lastgroup]
        yield token_class(match_groups[matcher.lastgroup])

    leftover = text[previous_end:]
    if leftover:
        yield LiteralToken(leftover)


def tokenize(text):
    return tuple(tokenize_iter(text))
