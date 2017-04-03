# -*- coding: utf-8 -*-
"""This module contains an implementation of template.

The main idea of the template is to run parsing of the text and store
AST tree, the result of the parsing. Also, it has a reference to the
environment. This is required for running of rendering routine.
"""


from curly import lexer
from curly import parser


class Template:
    """Template stored parsed and 'compiled' template.

    Using this class, you can render the template for different contexes
    without reparsing it each time.

    :param curly.env.Env env: Environment for the template.
    :param text: A template to compile.
    :type text: str or bytes
    :raises ValueError: if it is not possible to convert text into
        AST tree.
    """

    def __init__(self, text):
        self.node = parser.parse(lexer.tokenize(text))

    def __repr__(self):
        return repr(self.node)

    def render(self, context):
        """Render template into according to the given context.

        :param dict context: A dictionary with variables for the
            template.
        :return: Rendered template
        :rtype: str
        :raises ValueError: if it is not possible to render template
            with the given context.
        """
        return self.node.process(context)
