# -*- coding: utf-8 -*-
"""An implementation of Curly language.

Curly contains only 4 modules (including rudiment stuff for CLI):
lexing, parsing, template and utils.

The control flow is: to render the template, you need to create
an instance of :py:class:`curly.template.Template`. Template
has a parsed AST tree (it is created on its initialization
phase) of the real template and a number of routines (main is
:py:meth:`curly.template.Template.render`) to calculate the value of the
given template string.

How does :py:class:`curly.template.Template` got that AST tree?
Well, that's why you need lexing and parsing. Lexing splits raw text
string into a list of tokens: a typed classes which encapsulate a
chunks of text and describe them in terms of templating language (see
:py:func:`curly.lexer.tokenize`). Parsing takes the list of tokens and
makes tree structure with determined way of calculating template (only
environment and text are required.). Check :py:func:`curly.parser.parse`
for details.
"""


from curly.template import Template  # NOQA


def render(text, context):
    """Renders given text based on the context variables.

    This function uses :py:data:`curly.env.DEFAULT_ENV` as a default
    environment, build a template from the ``text`` parameter and
    renders it according to the ``context``.

    This is not the most effective method of calculating template
    because you need to parse it on any call. If you want the most
    efficient way, precompile template first.

    .. code-block:: pycon

      >>> from curly.template import Template
      >>> template = Template(text)
      >>> result1 = template.render(context1)
      >>> result2 = template.render(context2)

    :param text: Template text which you are going to render.
    :param dict context: A dictionary with a list of variables
        for template.
    :type text: str or bytes
    :return: Rendered template.
    :rtype: str
    :raises:
        :py:exc:`curly.exceptions.CurlyEvaluateError`: if it is not
        possible to evaluate expression within a context.

        :py:exc:`curly.exceptions.CurlyLexerError`: if it is not
        possible to perform lexing analysis of the template.

        :py:exc:`curly.exceptions.CurlyParserError`: if it is not
        possible to parse template.
    """
    return Template(text).render(context)
