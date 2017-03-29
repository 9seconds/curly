# -*- coding: utf-8 -*-


import curly.lexer


class Node:

    @classmethod
    def resolve_variable(cls, varname, context):
        if varname in context:
            return context[varname]

        chunks = varname.split(".", 1)
        if len(chunks) == 1:
            raise ValueError("Context {0!r} has no key {1!r}".format(
                context, varname))

        new_ctx = cls.resolve_variable(chunks[0], context)
        return cls.resolve_variable(chunks[1], new_ctx)

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
        self.resolve_variable(self.var, context)


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
        return self.resolve_variable(self.var, context)


class IfNode(VarNode):

    def emit(self, context):
        if context[self.var]:
            return super().emit(context)
        return ""


class LoopNode(VarNode):

    def emit(self, context):
        value = self.resolve_variable(self.var, context)

        if isinstance(value, dict):
            return self.emit_dict(value, context)

        return self.emit_iterable(value, context)

    def emit_dict(self, value, context):
        result = ""

        for key, val in sorted(value.items()):
            ctx = context.copy()
            ctx["item"] = {"key": key, "value": val}
            result += super().emit(ctx)

        return result

    def emit_iterable(self, value, context):
        result = ""

        for val in value:
            ctx = context.copy()
            ctx["item"] = val
            result += super().emit(ctx)

        return result


def parse(tokens):
    stack = []

    for token in tokens:
        if isinstance(token, (curly.lexer.LiteralToken)):
            stack.append(LiteralNode(token))
        elif isinstance(token, curly.lexer.PrintToken):
            stack.append(PrintNode(token))
        elif isinstance(token, curly.lexer.IfStartToken):
            stack.append(IfNode(token))
        elif isinstance(token, curly.lexer.LoopStartToken):
            stack.append(LoopNode(token))
        elif isinstance(token, curly.lexer.IfEndToken):
            ifnode, stack = rewind_stack(stack, search_for=IfNode)
            stack.append(ifnode)
        elif isinstance(token, curly.lexer.LoopEndToken):
            loopnode, stack = rewind_stack(stack, search_for=LoopNode)
            stack.append(loopnode)
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
            return node, stack
        nodes.append(node)

    if search_for is IfNode:
        raise ValueError("Incorrect closing if statement")
    raise ValueError("Incorrect closing loop statement")


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
    for tok in curly.lexer.tokenize(text):
        print(tok)
    print("--- HERE GO NODES\n")
    print(parse(curly.lexer.tokenize(text)))

    node = parse(curly.lexer.tokenize_iter(text))
    print("--- HERE GO RESULT\n")

    print(node.process(
        {
            "first_name": "Sergey",
            "last_name": "Arkhipov",
            "show_phone": True,
            "phone": "1289431439821342342",
            "verbose": True,
            "tada": "@!-",
            "like": [
                "1", "2", "3"
            ]
        }
    ))
