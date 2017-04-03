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


import collections
import pprint
import subprocess

from curly import lexer
from curly import utils


class ExpressionMixin:

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


class Node(collections.UserList):
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
        super().__init__()
        self.token = token
        self.done = False

    def __str__(self):
        return ("<{0.__class__.__name__}(done={0.done}, token={0.token!r}, "
                "data={0.data!r})>").format(self)

    def __repr__(self):
        return pprint.pformat(self._repr_rec())

    def _repr_rec(self):
        return {
            "raw_string": repr(self.token) if self.token else "",
            "type": self.__class__.__name__,
            "done": self.done,
            "nodes": [node._repr_rec() for node in self.data]}

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
        for node in self:
            yield from node.emit(context)


class RootNode(Node):

    def __init__(self, nodes):
        super().__init__(None)
        self.data = nodes
        self.done = True

    def __repr__(self):
        return pprint.pformat(self.data)


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

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["text"] = self.text

        return struct

    @property
    def text(self):
        return self.token.contents["text"]

    def emit(self, _):
        yield self.text


class PrintNode(ExpressionMixin, Node):
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

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["expression"] = self.expression

        return struct

    @property
    def expression(self):
        return self.token.contents["expression"]

    def emit(self, context):
        yield str(self.evaluated_expression(context))


class BlockTagNode(ExpressionMixin, Node):

    @property
    def function(self):
        return self.token.contents["function"]


class ConditionalNode(BlockTagNode):

    def __init__(self, token):
        super().__init__(token)
        self.ifnode = None

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["if"] = self.ifnode._repr_rec() if self.ifnode else {}

        return struct

    def emit(self, context):
        return self.ifnode.emit(context)


class IfNode(BlockTagNode):

    def __init__(self, token):
        super().__init__(token)
        self.elsenode = None

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["else"] = self.elsenode._repr_rec() if self.elsenode else {}
        struct["expression"] = self.expression

        return struct

    def emit(self, context):
        if self.evaluated_expression(context):
            return super().emit(context)
        elif self.elsenode:
            return self.elsenode.emit(context)


class ElseNode(BlockTagNode):
    pass


class LoopNode(BlockTagNode):

    def _repr_rec(self):
        struct = super()._repr_rec()
        struct["expression"] = self.expression

        return struct

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
            stack = parse_end_block_token(stack, token)
        else:
            raise ValueError("Unknown token {0}".format(token))

    for node in stack:
        if not node.done:
            raise ValueError(
                "Cannot find enclosement statement for {0.function}".format(
                    node))

    return RootNode(stack)


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


def parse_end_block_token(stack, token):
    function = token.contents["function"]

    if function == "if":
        return parse_end_if_token(stack, token)
    elif function == "loop":
        return parse_end_loop_token(stack, token)
    else:
        raise ValueError(
            "Unknown end block tag {0}".format(token.raw_string))


def parse_start_if_token(stack, token):
    stack.append(ConditionalNode(token))
    stack.append(IfNode(token))

    return stack


def parse_start_elif_token(stack, token):
    stack = rewind_stack_for(stack, search_for=IfNode)
    stack.append(IfNode(token))

    return stack


def parse_start_else_token(stack, token):
    stack = rewind_stack_for(stack, search_for=IfNode)
    stack.append(ElseNode(token))

    return stack


def parse_start_loop_token(stack, token):
    stack.append(LoopNode(token))

    return stack


def parse_end_if_token(stack, token):
    stack = rewind_stack_for(stack, search_for=(IfNode, ElseNode))
    stack = rewind_stack_for(stack, search_for=ConditionalNode)

    cond = stack.pop()
    previous_node, *rest_nodes = cond
    for next_node in rest_nodes:
        if isinstance(previous_node, ElseNode):
            raise ValueError(
                "If statement {0} has multiple elses".format(
                    cond[0].raw_string))
        previous_node.elsenode = next_node
        previous_node = next_node

    stack.append(cond[0])

    return stack


def parse_end_loop_token(stack, token):
    return rewind_stack_for(stack, search_for=LoopNode)


def rewind_stack_for(stack, *, search_for):
    nodes = []
    node = None

    while stack:
        node = stack.pop()
        if not node.done:
            break
        nodes.append(node)
    else:
        raise ValueError("Cannot find matching start statement")

    if not isinstance(node, search_for):
        raise ValueError(
            "Expected to find loop start statement, got {0}".format(node))

    node.done = True
    node.data = nodes[::-1]
    stack.append(node)

    return stack
