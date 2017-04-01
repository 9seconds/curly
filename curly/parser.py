# -*- coding: utf-8 -*-


import subprocess

from curly import lexer
from curly import utils


class Node:

    __slots__ = "token", "nodes", "ready"

    NAME = "node"

    def __init__(self, token):
        self.token = token
        self.nodes = []
        self.ready = False

    def __str__(self):
        return ("<{0.__class__.__name__}(ready={0.ready}, token={0.token!r}, "
                "nodes={0.nodes!r})>").format(self)

    def __repr__(self):
        return str(self)

    @property
    def raw_string(self):
        return self.token.raw_string

    def process(self, env, context):
        return "".join(self.emit(env, context))

    def emit(self, env, context):
        for node in self.nodes:
            yield from node.emit(env, context)

    def validate_context(self, env, context):
        pass


class LiteralNode(Node):

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    @property
    def text(self):
        return self.token.contents["text"]

    def emit(self, env, context):
        yield self.text


class PrintNode(Node):

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    @property
    def expression(self):
        return self.token.contents["expression"]

    def emit(self, env, context):
        value = subprocess.list2cmdline(self.expression)
        yield str(utils.resolve_variable(value, context))


class BlockTagNode(Node):

    @property
    def expression(self):
        return self.token.contents["expression"]

    @property
    def function(self):
        return self.token.contents["function"]

    def emit(self, env, context):
        function = env.get(self.function)

        if not callable(function):
            raise ValueError(
                "Cannot find callable function {0} in environment".format(
                    function))

        yield from function(self, env, context)


def parse(tokens):
    stack = []

    for token in tokens:
        if isinstance(token, lexer.LiteralToken):
            stack.append(LiteralNode(token))
        elif isinstance(token, lexer.PrintToken):
            stack.append(PrintNode(token))
        elif isinstance(token, lexer.StartBlockToken):
            stack.append(BlockTagNode(token))
        elif isinstance(token, lexer.EndBlockToken):
            stack = rewind_stack(stack, token)
        else:
            raise ValueError("Unknown token {0}".format(token))

    for node in stack:
        if not node.ready:
            raise ValueError(
                "Cannot find enclosement statement for {0.function}".format(
                    node))

    root = Node(None)
    root.nodes = stack

    return root


def rewind_stack(stack, end_token):
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
            "got {1} instead".format(node.function,
                                     end_token.contents["function"]))

    node.ready = True
    node.nodes = nodes[::-1]
    stack.append(node)

    return stack
