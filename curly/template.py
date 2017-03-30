# -*- coding: utf-8 -*-


from curly import lexer
from curly import parser


class Template:

    def __init__(self, text):
        self.node = parser.parse(lexer.tokenize_iter(text))

    def render(self, context):
        return self.node.process(context)

    def __getstate__(self):
        return self.node

    def __setstate__(self, state):
        self.node = state


def render(text, context):
    return Template(text).render(context)
