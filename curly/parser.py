# -*- coding: utf-8 -*-


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
        return ("<{0.__class__.__name__}(token={0.token!r}, "
                "nodes={0.nodes!r})>").format(self)

    def __repr__(self):
        return str(self)

    def process(self, context):
        self.validate_context(context)
        return "".join(self.emit(context))

    def emit(self, context):
        for node in self.nodes:
            yield from node.emit(context)

    def validate_context(self, context):
        pass


class VarNode(Node):

    @property
    def var(self):
        return self.token.contents["var"]

    def validate_context(self, context):
        utils.resolve_variable(self.var, context)


class LiteralNode(Node):

    NAME = "literal"

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        yield self.token.contents["text"]


class PrintNode(VarNode):

    NAME = "print tag"

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        yield str(utils.resolve_variable(self.var, context))


class IfNode(VarNode):

    NAME = "if"

    def emit(self, context):
        if utils.resolve_variable(self.var, context):
            yield from super().emit(context)
        else:
            yield ""


class LoopNode(VarNode):

    NAME = "loop"

    def emit(self, context):
        value = utils.resolve_variable(self.var, context)

        context_copy = context.copy()
        if isinstance(value, dict):
            yield from self.emit_dict(value, context_copy)
        else:
            yield from self.emit_iterable(value, context_copy)

    def emit_dict(self, value, context):
        for key, val in sorted(value.items()):
            context["item"] = {"key": key, "value": val}
            yield from super().emit(context)

    def emit_iterable(self, value, context):
        for val in value:
            context["item"] = val
            yield from super().emit(context)


def parse(tokens):
    stack = []

    for token in tokens:
        if isinstance(token, lexer.LiteralToken):
            stack.append(LiteralNode(token))
        elif isinstance(token, lexer.PrintToken):
            stack.append(PrintNode(token))
        elif isinstance(token, lexer.IfStartToken):
            stack.append(IfNode(token))
        elif isinstance(token, lexer.LoopStartToken):
            stack.append(LoopNode(token))
        elif isinstance(token, lexer.IfEndToken):
            stack = rewind_stack(stack, search_for=IfNode)
        elif isinstance(token, lexer.LoopEndToken):
            stack = rewind_stack(stack, search_for=LoopNode)
        else:
            raise ValueError("Unknown token {0!r}".format(token))

    for node in stack:
        if not node.ready:
            raise ValueError(
                "Cannot find enclosement statement for {0.NAME}".format(
                    node))

    root = Node(None)
    root.nodes = stack

    return root


def rewind_stack(stack, *, search_for):
    nodes = []

    while stack:
        node = stack.pop()
        if not node.ready:
            break
        nodes.append(node)
    else:
        raise ValueError(
            "Cannot find matching {0.NAME} start statement".format(search_for))

    if not isinstance(node, search_for):
        raise ValueError(
            ("Expected to find matching {0.NAME} statement, "
             "got {1.NAME} instead").format(search_for, node))

    node.ready = True
    node.nodes = nodes[::-1]
    stack.append(node)

    return stack
