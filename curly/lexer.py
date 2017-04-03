# -*- coding: utf-8 -*-
"""Lexer has one of the main Curly's functions, :py:func:`tokenize`.

The main idea of lexing is to split raw text into structured list of
well known and defined parts, called *tokens*. Each token has a class
and some contents (let's say, from ``{% if something %}`` we can get
following contents for :py:class:`StartBlockToken`: ``if`` as a function
name and ``["something"]`` as a block expression).

Here is the example:

.. code-block:: python3

  >>> from curly.lexer import tokenize
  >>> text = '''\\
  ...     Hello! My name is {{ name }}.\\
  ... {% if likes %}And I like these things: {% loop likes %}\\
  ... {{ item }},{% /loop %}{% /if %}'''
  >>> for token in tokenize(text):
  ...     print(repr(token))
  ...
  <LiteralToken(raw='    Hello! My name is ', \
contents={'text': '    Hello! My name is '})>
  <PrintToken(raw='{{ name }}', contents={'expression': ['name']})>
  <LiteralToken(raw='.', contents={'text': '.'})>
  <StartBlockToken(raw='{% if likes %}', \
contents={'function': 'if', 'expression': ['likes']})>
  <LiteralToken(raw='And I like these things: ', \
contents={'text': 'And I like these things: '})>
  <StartBlockToken(raw='{% loop likes %}', \
contents={'function': 'loop', 'expression': ['likes']})>
  <PrintToken(raw='{{ item }}', contents={'expression': ['item']})>
  <LiteralToken(raw=',', contents={'text': ','})>
  <EndBlockToken(raw='{% /loop %}', contents={'function': 'loop'})>
  <EndBlockToken(raw='{% /if %}', contents={'function': 'if'})>
  >>>

Some terminology:

*function*
  Function is the name of function to call within a block. For example,
  in block tag ``{% if something %}`` function is ``if``.

*expression*
  Expression is the something to print or to pass to function. For
  example, in block tag ``{% if lala | blabla | valueof "qq pp" %}``,
  expression is ``lala | blabla | valueof "qq pp"``. Usually, expression
  is parsed according to POSIX shell lexing: ``["lala", "|", "blabla",
  "|", "valueof", "qq pp"]``.

  It is out of the scope of the Curly is how to implement evaluation
  of the expression. By default, curly tries to find it in
  context literally, but if you want, feel free to implement your
  own Jinja2-style DSL. Or even call :py:func:`ast.parse` with
  :py:func:`compile`.

For details on lexing please check :py:func:`tokenize` function.
"""


import collections
import functools

from curly import utils


REGEXP_FUNCTION = r"[a-zA-Z0-9_-]+"
"""Regular expression for function definition."""

REGEXP_EXPRESSION = r"(?:\\.|[^\{\}])+"
"""Regular expression for 'expression' definition."""


class Token(collections.UserString):
    """Base class for every token to parse.

    Token is parsed by :py:func:`tokenize` only if it has defined REGEXP
    attribute.

    :param str raw_string: Text which was recognized as a token.
    :raises ValueError: if ``raw_string`` does not match for
        some reason.
    """

    __slots__ = "contents", "raw_string"

    REGEXP = None

    def __init__(self, raw_string):
        matcher = self.REGEXP.match(raw_string)
        if matcher is None:
            raise ValueError(
                "String {0!r} is not valid for pattern {1!r}".format(
                    raw_string, self.REGEXP.pattern))

        super().__init__(raw_string)
        self.contents = self.extract_contents(matcher)

    def extract_contents(self, matcher):
        """Extract more detail token information from regular expression.

        :param re.match matcher: Regular expression matcher.
        :return: A details on the token.
        :rtype: dict[str, str]
        """
        return {}

    def __repr__(self):
        return ("<{0.__class__.__name__}(raw={0.data!r}, "
                "contents={0.contents!r})>").format(self)


class PrintToken(Token):
    """Responsible for matching of print tag ``{{ var }}``.

    The contents of the block is the *expression* which should be
    printed. In ``{{ var }}`` it is ``["var"]``. Regular expression for
    *expression* is :py:data:`REGEXP_EXPRESSION`.
    """
    REGEXP = utils.make_regexp(
        r"""
        {{\s*  # open {{
        (%s)  # expression 'var' in {{ var }}
        \s*}}    # closing }}
        """ % REGEXP_EXPRESSION)
    """Regular expression of the token."""

    def extract_contents(self, matcher):
        return {"expression": utils.make_expression(matcher.group(1))}


class StartBlockToken(Token):
    """Responsible for matching of start function call block tag.

    In other words, it matches ``{% function expr1 expr2 expr3... %}``.

    The contents of the block is the *function* and *expression*.
    Regular expression for *function* is :py:data:`REGEXP_FUNCTION`, for
    expression: :py:data:`REGEXP_EXPRESSION`.
    """
    REGEXP = utils.make_regexp(
        r"""
        {%%\s*  # open block tag
        (%s)    # function name
        (%s)?   # expression for function
        \s*%%}  # closing block tag
        """ % (REGEXP_FUNCTION, REGEXP_EXPRESSION))
    """Regular expression of the token."""

    def extract_contents(self, matcher):
        return {
            "function": matcher.group(1).strip(),
            "expression": utils.make_expression(matcher.group(2))}


class EndBlockToken(Token):
    """Responsible for matching of ending function call block tag.

    In other words, it matches ``{% /function %}``.

    The contents of the block is the *function* (regular expression is
    :py:data:`REGEXP_FUNCTION`).
    """
    REGEXP = utils.make_regexp(
        r"""
        {%%\s*  # open block tag
        /\s*    # / character
        (%s)    # function name
        \s*%%}  # closing block tag
        """ % REGEXP_FUNCTION)
    """Regular expression of the token."""

    def extract_contents(self, matcher):
        return {"function": matcher.group(1).strip()}


class LiteralToken(Token):
    """Responsible for parts of the texts which are literal.

    Literal part of the text should be printed as is, they are context
    undependend and not enclosed in any tag. Otherwise: they are placed
    outside any tag.

    For example, in the template ``{{ first_name }} - {{ last_name }}``,
    literal token is " - " (yes, with spaces).
    """
    TEXT_UNESCAPE = utils.make_regexp(r"\\(.)")

    def __init__(self, text):
        self.data = text
        self.contents = {"text": self.TEXT_UNESCAPE.sub(r"\1", text)}


def tokenize(text):
    """Lexical analysis of the given text.

    Main lexing function: it takes text and returns iterator to
    the produced tokens. There are several facts you have to
    know about this function:

    #. It does not raise exceptions. If something goes fishy,
       tokenizer fallbacks to :py:class:`LiteralToken`.
    #. It uses one big regular expression, taken from
       :py:func:`make_tokenizer_regexp`. This regular expression
       looks like this:

       ::

         (?P<SomeToken>{%\s*(\S+)\s*%})|(?P<AnotherToken>{{\s*(\w+)\s*}})

    #. Actually, function searches only for template tokens,
       emiting of :py:class:`LiteralToken` is a side effect.

    The logic of the function is quite simple:

    #. It gets expression to match from
       :py:func:`make_tokenizer_regexp`.
    #. Function starts to traverse the text using
       :py:meth:`re.regex.finditer` method. It yields non-overlapping
       matches for the regular expression.
    #. When match is found, we are trying to check if we've emit
       :py:class:`LiteralToken` for the text before. Let's say,
       we have a text like that:

       ::

         'Hello, {{ var }}'

       First match on iteration of
       :py:meth:`re.regex.finditer` will be for "{{ var }}",
       so we've jumped over "Hello, " substring. To emit
       this token, we need to remember position where last
       match was made (:py:meth:`re.match.end`, safe to start with 0)
       and where new one is occured (:py:meth:`re.match.start`).

       So ``text[previous_end:matcher.start(0)]`` is our
       text "Hello, " which goes for :py:class:`LiteralToken`.
    #. When we stop iteration, we need to check if we have any
       leftovers after. This could be done emiting :py:class:`LiteralToken`
       with ``text[previous_end:]`` text (if it is non empty, obviously).

    :param text: Text to lex into tokens.
    :type text: str or bytes
    :return: Generator with :py:class:`Token` instances.
    :rtype: Generator[:py:class:`Token`]
    """
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
    """Create regular expression for :py:func:`tokenize`.

    This small wrapper takes a list of know tokens and their regular
    expressions and concatenates them into one big expression.

    :return: Regular expression for :py:func:`tokenize` function.
    :rtype: :py:class:`re.regex`
    """
    patterns = get_token_patterns()
    patterns = [
        "(?P<{0}>{1})".format(k, v.REGEXP.pattern)
        for k, v in patterns.items()]
    patterns = "|".join(patterns)
    patterns = utils.make_regexp(patterns)

    return patterns


@functools.lru_cache(1)
def get_token_patterns():
    """Mapping of pattern name to its class.

    :return: Mapping of the known tokens with regular expressions.
    :rtype: dict[str, Token]
    """
    return get_token_patterns_rec(Token)


def get_token_patterns_rec(cls):
    patterns = {}

    for scls in cls.__subclasses__():
        patterns.update(get_token_patterns_rec(scls))
        if scls.REGEXP is not None:
            patterns[scls.__name__] = scls

    return patterns
