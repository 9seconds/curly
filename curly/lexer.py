# -*- coding: utf-8 -*-


import functools

from curly import utils


REGEXP_FUNCTION = r"[a-zA-Z0-9_-]+"
REGEXP_EXPRESSION = r"(?:\\.|[^\{\}])+"


class Token:

    __slots__ = "contents", "raw_string"

    REGEXP = None

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


class PrintToken(Token):
    REGEXP = utils.make_regexp(
        r"""
        {{\s*  # open {{
        (%s)  # expression 'var' in {{ var }}
        \s*}}    # closing }}
        """ % REGEXP_EXPRESSION)

    def extract_contents(self, matcher):
        return {"expression": utils.make_expression(matcher.group(1))}


class StartBlockToken(Token):
    REGEXP = utils.make_regexp(
        r"""
        {%%\s*  # open block tag
        (%s)    # function name
        (%s)?   # expression for function
        \s*%%}  # closing block tag
        """ % (REGEXP_FUNCTION, REGEXP_EXPRESSION))

    def extract_contents(self, matcher):
        return {
            "function": matcher.group(1).strip(),
            "expression": utils.make_expression(matcher.group(2))}


class EndBlockToken(Token):
    REGEXP = utils.make_regexp(
        r"""
        {%%\s*  # open block tag
        /\s*    # / character
        (%s)    # function name
        \s*%%}  # closing block tag
        """ % REGEXP_FUNCTION)

    def extract_contents(self, matcher):
        return {"function": matcher.group(1).strip()}


class LiteralToken(Token):

    TEXT_UNESCAPE = utils.make_regexp(r"\\(.)")

    def __init__(self, text):
        self.raw_string = text
        self.contents = {"text": self.TEXT_UNESCAPE.sub(r"\1", text)}


def tokenize(text):
    previous_end = 0
    tokens = get_token_patterns()
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    for matcher in make_tokenizer_regexp().finditer(text):
        if matcher.start(0) != previous_end:
            yield LiteralToken(text[previous_end:matcher.start(0)])
        previous_end = matcher.end(0)

        match_groups = matcher.groupdict()
        token_class = tokens[matcher.lastgroup]
        yield token_class(match_groups[matcher.lastgroup])

    leftover = text[previous_end:]
    if leftover:
        yield LiteralToken(leftover)


@functools.lru_cache(1)
def make_tokenizer_regexp():
    patterns = get_token_patterns()
    patterns = [
        "(?P<{0}>{1})".format(k, v.REGEXP.pattern)
        for k, v in patterns.items()]
    patterns = "|".join(patterns)
    patterns = utils.make_regexp(patterns)

    return patterns


@functools.lru_cache(1)
def get_token_patterns():
    return get_token_patterns_rec(Token)


def get_token_patterns_rec(cls):
    patterns = {}

    for scls in cls.__subclasses__():
        patterns.update(get_token_patterns_rec(scls))
        if scls.REGEXP is not None:
            patterns[scls.__name__] = scls

    return patterns
