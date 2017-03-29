# -*- coding: utf-8 -*-


import curly.lexer
import curly.parser


class Template:

    def __init__(self, text):
        tokens = curly.lexer.tokenize_iter(text)
        self.node = curly.parser.parse(tokens)

    def render(self, context):
        return self.node.process(context)

    def __getstate__(self):
        return self.node

    def __setstate__(self, state):
        self.node = state


def render(text, context):
    return Template(text).render(context)
