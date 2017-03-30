# -*- coding: utf-8 -*-


from curly import lexer
from curly import parser


class Template:

    def __init__(self, text):
        self.node = parser.parse(lexer.tokenize_iter(text))

    def render(self, context):
        return self.node.process(context)


def render(text, context):
    return Template(text).render(context)
