# -*- coding: utf-8 -*-


import collections
import re
import textwrap


def make_regexp(pattern):
    pattern = textwrap.dedent(pattern)
    pattern = re.compile(pattern, re.UNICODE | re.VERBOSE)

    return pattern


class Token:

    __slots__ = "contents", "raw_string"

    REGEXP = make_regexp(".+")

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
    REGEXP = make_regexp(
        r"""
        \{\{                        # opening {{
        ([a-zA-Z0-9_ \t\n\r\f\v]+)  # group 1, 'var' in {{ var }}
        \}\}                        # closing }}
        """
    )

    def extract_contents(self, matcher):
        return {"var": matcher.group(1).strip()}


class IfStartToken(Token):
    REGEXP = make_regexp(
        r"""
        \{\?                        # opening {?
        ([a-zA-Z0-9_ \t\n\r\f\v]+)  # group 1, 'var' in {? var ?}
        \?\}                        # closing ?}
        """
    )

    def extract_contents(self, matcher):
        return {"var": matcher.group(1).strip()}


class IfEndToken(Token):
    REGEXP = make_regexp(r"\{\?\}")


class LoopStartToken(Token):
    REGEXP = make_regexp(
        r"""
        \{\%                        # opening {%
        ([a-zA-Z0-9_ \t\n\r\f\v]+)  # group 1, 'var' in {% var %}
        \%\}                        # closing %}
        """
    )

    def extract_contents(self, matcher):
        return {"var": matcher.group(1).strip()}


class LoopEndToken(Token):
    REGEXP = make_regexp(r"\{%\}")


class LiteralToken(Token):

    def __init__(self, text):
        self.raw_string = text
        self.contents = {"text": text}


TOKENS = collections.OrderedDict()
TOKENS["print"] = PrintToken
TOKENS["if_start"] = IfStartToken
TOKENS["if_end"] = IfEndToken
TOKENS["loop_start"] = LoopStartToken
TOKENS["loop_end"] = LoopEndToken

TOKENIZER_REGEXP = make_regexp(
    "|".join(
        "(?P<{0}>{1})".format(k, v.REGEXP.pattern) for k, v in TOKENS.items()
     )
)


def tokenize(text):
    print(TOKENIZER_REGEXP.pattern)
    return tuple(tokenize_iter(text))


def tokenize_iter(text):
    previous_end = 0

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



if __name__ == "__main__":
    text = """
    Hello, world! This is {{ first_name }} {{ last_name }}
    {? show_phone ?}
      {{ phone }}
    {?} {?

    And here is the list of stuff I like:
    {% like %}
      - {{ item }} \{\{sdfsd {?verbose?}{{ tada }}!{?}
    {%}

    Thats all!
    """.strip()
    print("--- TEXT:\n{0}\n---".format(text))
    print("--- HERE GO TOKENS\n")
    for tok in tokenize(text):
        print(tok)
