# -*- coding: utf-8 -*-


import curly.lexer
import curly.utils


class Node:

    __slots__ = "token", "nodes", "ready"

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
        return self.emit(context)

    def emit(self, context):
        return "".join(str(node.emit(context)) for node in self.nodes)

    def validate_context(self, context):
        pass


class VarNode(Node):

    @property
    def var(self):
        return self.token.contents["var"]

    def validate_context(self, context):
        curly.utils.resolve_variable(self.var, context)


class LiteralNode(Node):

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        return self.token.contents["text"]


class PrintNode(VarNode):

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        return curly.utils.resolve_variable(self.var, context)


class IfNode(VarNode):

    def emit(self, context):
        if curly.utils.resolve_variable(self.var, context):
            return super().emit(context)
        return ""


class LoopNode(VarNode):

    def emit(self, context):
        value = curly.utils.resolve_variable(self.var, context)

        if isinstance(value, dict):
            iterable = self.emit_dict(value, context)
        else:
            iterable = self.emit_iterable(value, context)

        return "".join(iterable)

    def emit_dict(self, value, context):
        for key, val in sorted(value.items()):
            new_context = context.copy()
            new_context["item"] = {"key": key, "value": val}
            yield super().emit(new_context)

    def emit_iterable(self, value, context):
        for val in value:
            new_context = context.copy()
            new_context["item"] = val
            yield super().emit(new_context)


def parse(tokens):
    stack = []

    for token in tokens:
        if isinstance(token, curly.lexer.LiteralToken):
            stack.append(LiteralNode(token))
        elif isinstance(token, curly.lexer.PrintToken):
            stack.append(PrintNode(token))
        elif isinstance(token, curly.lexer.IfStartToken):
            stack.append(IfNode(token))
        elif isinstance(token, curly.lexer.LoopStartToken):
            stack.append(LoopNode(token))
        elif isinstance(token, curly.lexer.IfEndToken):
            stack = rewind_stack(stack, search_for=IfNode)
        elif isinstance(token, curly.lexer.LoopEndToken):
            stack = rewind_stack(stack, search_for=LoopNode)
        else:
            raise ValueError("Unknown token {0!r}".format(token))

    root = Node(None)
    root.nodes = stack

    return root


def rewind_stack(stack, *, search_for):
    nodes = []

    while stack:
        node = stack.pop()
        if isinstance(node, search_for) and not node.ready:
            node.ready = True
            node.nodes = nodes
            stack.append(node)
            return stack
        nodes.append(node)

    if search_for is IfNode:
        raise ValueError("Incorrect closing if statement")
    raise ValueError("Incorrect closing loop statement")
