# -*- coding: utf-8 -*-


from curly import lexer
from curly import parser


class Template:

    __slots__ = "env", "node"

    def __init__(self, env, text):
        self.node = parser.parse(lexer.tokenize(text))
        self.env = env

    def render(self, context):
        return self.node.process(self.env, context)
