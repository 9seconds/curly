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
        utils.resolve_variable(self.var, context)


class LiteralNode(Node):

    NAME = "literal"
    TEXT_UNESCAPE = utils.make_regexp(r"\\(.)")

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        return self.TEXT_UNESCAPE.sub(r"\1", self.token.contents["text"])


class PrintNode(VarNode):

    NAME = "print tag"

    def __init__(self, token):
        super().__init__(token)
        self.ready = True

    def emit(self, context):
        return utils.resolve_variable(self.var, context)


class IfNode(VarNode):

    NAME = "if"

    def emit(self, context):
        if utils.resolve_variable(self.var, context):
            return super().emit(context)
        return ""


class LoopNode(VarNode):

    NAME = "loop"

    def emit(self, context):
        value = utils.resolve_variable(self.var, context)

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
