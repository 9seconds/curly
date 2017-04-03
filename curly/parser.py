# -*- coding: utf-8 -*-
"""Parser has another main Curly's function, :py:func:`parse`.

The main idea of parsing is to take a stream of
tokens and convert it into `abstract syntax tree
<https://en.wikipedia.org/wiki/Abstract_syntax_tree>`_. Each node in the
tree is present by :py:class:`Node` instances and each instance has a
list of nodes (therefore - tree).

:py:func:`parse` produces such tree and it is possible to render it with
method :py:meth:`Node.process`.

Example:

.. code-block:: python3

  >>> from curly.lexer import tokenize
  >>> from curly.parser import parse
  >>> text = '''\\
  ...     Hello! My name is {{ name }}.\\
  ... {% if likes %}And I like these things: {% loop likes %}\\
  ... {{ item }},{% /loop %}{% /if %}'''
  >>> tokens = tokenize(text)
  >>> print(parse(tokens))
  <Node(ready=False, token=None, nodes=[{'finished': True,
   'nodes': [],
   'token': <LiteralToken(raw='  Hello! My name is ', contents={'text': \
'  Hello! My name is '})>}, {'finished': True,
   'nodes': [],
   'token': <PrintToken(raw='{{ name }}', \
contents={'expression': ['name']})>}, {'finished': True,
   'nodes': [],
   'token': <LiteralToken(raw='.', contents={'text': '.'})>}, \
{'finished': True,
   'nodes': [{'finished': True,
              'nodes': [],
              'token': <LiteralToken(raw='And I like these things: \
', contents={'text': 'And I like these things: '})>},
             {'finished': True,
              'nodes': [{'finished': True,
                         'nodes': [],
                         'token': <PrintToken(raw='{{ item }}', \
contents={'expression': ['item']})>},
                        {'finished': True,
                         'nodes': [],
                         'token': <LiteralToken(raw=',', \
contents={'text': ','})>}],
              'token': <StartBlockToken(raw='{% loop likes %}', \
contents={'expression': ['likes'], 'function': 'loop'})>}],
   'token': <StartBlockToken(raw='{%if likes %}', \
contents={'expression': ['likes'], 'function': 'if'})>}])>
"""


import pprint
import subprocess

from curly import lexer
from curly import utils


class Node:
    """Node of an AST tree.

    It has 2 methods for rendering of the node content:
    :py:meth:`Node.emit` and :py:meth:`Node.process`. First one
    is the generator over the rendered content, second one just
    concatenates them into a single string. So, if you defines your
    own node type, you want to define :py:meth:`Noed.emit` only,
    :py:meth:`Node.process` stays the same.

    If you want to render template to the string, use
    :py:meth:`Node.process`. This is a thing you are looking for.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.Token`
    """

    __slots__ = "token", "nodes", "done"

    def __init__(self, token):
        self.token = token
        self.nodes = []
        self.done = False

    def __str__(self):
        return ("<{0.__class__.__name__}(done={0.done}, token={0.token!r}, "
                "nodes={0.nodes!r})>").format(self)

    def __repr__(self):
        return pprint.pformat(self._repr_rec())

    def _repr_rec(self):
        return {
            "token": self.token,
            "done": self.done,
            "nodes": [node._repr_rec() for node in self.nodes]}

    @property
    def raw_string(self):
        """Return a raw content of the related token.

        For example, for token ``{{ var }}`` it returns literally ``{{
        var }}``.

        :return: Raw content of the token.
        :rtype: str
        """
        return self.token.raw_string

    def process(self, context):
        """Return rendered content of the node as a string.

        :param dict context: Dictionary with a context variables.
        :return: Rendered template
        :rtype: str
        """
        return "".join(self.emit(context))

    def emit(self, context):
        """Return generator which emits rendered chunks of text.

        Axiom: ``"".join(self.emit(context)) == self.process(context)``

        :param dict context: Dictionary with a context variables.
        :return: Generator with rendered texts.
        :rtype: Generator[str]
        """
        for node in self.nodes:
            yield from node.emit(context)


class LiteralNode(Node):
    """Node which presents literal text.

    This is one-to-one representation of
    :py:class:`curly.lexer.LiteralToken` in AST tree.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.LiteralToken`
    """

    def __init__(self, token):
        super().__init__(token)
        self.done = True

    @property
    def text(self):
        return self.token.contents["text"]

    def emit(self, _):
        yield self.text


class PrintNode(Node):
    """Node which presents print token.

    This is one-to-one representation of
    :py:class:`curly.lexer.PrintToken` in AST tree. Example of such node
    is the node for ``{{ var }}`` token.

    :param token: Token which produced that node.
    :type token: :py:class:`curly.lexer.PrintToken`
    """

    def __init__(self, token):
        super().__init__(token)
        self.done = True

    @property
    def expression(self):
        return self.token.contents["expression"]

    def emit(self, context):
        value = subprocess.list2cmdline(self.expression)
        yield str(utils.resolve_variable(value, context))


class BlockTagNode(Node):

    @property
    def expression(self):
        return self.token.contents["expression"]

    @property
    def function(self):
        return self.token.contents["function"]

    def evaluated_expression(self, context):
        value = subprocess.list2cmdline(self.expression)
        value = utils.resolve_variable(value, context)

        return value


class ConditionalNode(BlockTagNode):

    def __init__(self, token):
        super().__init__(token)
        self.ifnode = None

    def emit(self, context):
        if self.ifnode is not None:
            yield from self.ifnode.emit(context)


class IfNode(BlockTagNode):

    def __init__(self, token):
        super().__init__(token)
        self.elsenode = None

    def emit(self, context):
        if self.evaluated_expression(context):
            yield from super().emit(context)
        elif self.elsenode:
            yield from self.elsenode.emit(context)


class ElseNode(BlockTagNode):
    pass


class LoopNode(BlockTagNode):

    def emit(self, context):
        resolved = self.evaluated_expression(context)
        context_copy = context.copy()

        if isinstance(resolved, dict):
            for key, value in sorted(resolved.items()):
                context_copy["item"] = {"key": key, "value": value}
                yield from super().emit(context_copy)
        else:
            for item in resolved:
                context_copy["item"] = item
                yield from super().emit(context_copy)


def parse(tokens):
    stack = []

    for token in tokens:
        if isinstance(token, lexer.LiteralToken):
            stack = parse_literal_token(stack, token)
        elif isinstance(token, lexer.PrintToken):
            stack = parse_print_token(stack, token)
        elif isinstance(token, lexer.StartBlockToken):
            stack = parse_start_block_token(stack, token)
        elif isinstance(token, lexer.EndBlockToken):
            stack = rewind_stack_for_end_block(stack, token)
        else:
            raise ValueError("Unknown token {0}".format(token))

    for node in stack:
        if not node.done:
            raise ValueError(
                "Cannot find enclosement statement for {0.function}".format(
                    node))

    root = Node(None)
    root.nodes = stack

    return root


def parse_literal_token(stack, token):
    stack.append(LiteralNode(token))

    return stack


def parse_print_token(stack, token):
    stack.append(PrintNode(token))

    return stack


def parse_start_block_token(stack, token):
    function = token.contents["function"]

    if function == "if":
        return parse_start_if_token(stack, token)
    elif function == "elif":
        return parse_start_elif_token(stack, token)
    elif function == "else":
        return parse_start_else_token(stack, token)
    elif function == "loop":
        return parse_start_loop_token(stack, token)
    else:
        raise ValueError(
            "Unknown block tag {0}".format(token.raw_string))


def rewind_stack_for_end_block(stack, end_token):
    nodes = []

    while stack:
        node = stack.pop()
        if not node.ready:
            break
        nodes.append(node)
    else:
        raise ValueError(
            "Cannot find matching {0} start statement".format(
                end_token.contents["function"]))

    if node.function != end_token.contents["function"]:
        raise ValueError(
            "Expected to find {0} start statement, "
            "got {1} instead".format(
                node.function, end_token.contents["function"]))

    node.ready = True
    node.nodes = nodes[::-1]
    stack.append(node)

    return stack
