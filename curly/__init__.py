# -*- coding: utf-8 -*-
"""An implementation of Curly language.

Curly contains only 5 modules (including rudiment stuff for CLI):
lexing, parsing, environment, template and utils.

The control flow is like this: to render the template, you need to have
:py:class:`curly.env.Env` instance. The main idea of the environment
instance is to support function call tags (these ``{% func expression
%}...{% /func %}``). Basically, environment is just a collection of such
functions.

After that (or before that, doesn't matter, environment is required
only to calculate the value of the template along with context),
you can create an instance of :py:class:`curly.template.Template`.
Template has a parsed AST tree (it is created on its initialization
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
from curly.env import Env  # NOQA
from curly.env import DEFAULT_ENV


def render(text, context):
    """Renders given text based on the context variables.

    This function uses :py:data:`curly.env.DEFAULT_ENV` as a default
    environment, build a template from the ``text`` parameter and
    renders it according to the ``context``.

    This is not the most effective method of calculating template
    because you need to parse it on any call. If you want the most
    efficient way, precompile template first.

    .. code-block:: pycon

      >>> from curly.env import DEFAULT_ENV
      >>> template = DEFAULT_ENV.template(text)
      >>> result1 = template.render(context1)
      >>> result2 = template.render(context2)

    :param text: Template text which you are going to render
    :param dict context: A dictionary with a list of variables
        for template
    :type text: str or bytes
    :return: Rendered template
    :rtype: str
    :raises ValueError: if template is impossible to render
    """
    return DEFAULT_ENV.template(text).render(context)
