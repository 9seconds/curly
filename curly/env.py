# -*- coding: utf-8 -*-
"""This module contains implementation of Curly template environment.

All functions, mentioned here (:py:func:`env_if`, :py:func:`env_ifnot`
and :py:func:`env_loop`) are reference simple implementation. For
example, conditionals do not support ``else`` clauses and loops have no
convenient ``index``, ``first`` and ``last`` stuff. It is fine.

All functions for function calls should match following signature:

.. code-block:: python3

  def my_method(parser_node, env_instance, context):
      yield ""

All such functions should return iterator or iterable. Function emits
the chunks of text (they will be concatenated at the end with simple
``"".join(...)``) related to the ``parser_node``.

``parser_node`` is the instance of :py:class:`curly.parser.Node`. For
subnodes please check its ``nodes`` attribute. ``env_instance`` -
instance of :py:class:`Env` (if you need to search something in it).
``context`` is the context.
"""


import collections.abc
import subprocess

from curly import template
from curly import utils


class Env(collections.abc.Mapping):
    """Environment is the collection of functions.

    These functions would be avaialble for function call AST nodes.

    :param functions: A mapping with functions available for end user.
    :type functions: dict or None
    """

    __slots__ = "functions",

    def __init__(self, functions=None):
        self.functions = {
            "if": env_if,
            "if-not": env_ifnot,
            "loop": env_loop
        }
        self.functions.update(functions or {})

    def __getitem__(self, key):
        return self.functions[key]

    def __iter__(self):
        return iter(self.functions)

    def __len__(self):
        return len(self.functions)

    def __contains__(self, key):
        return key in self.functions

    def template(self, text):
        """Create template based on that environment.

        :param text: Template to render.
        :type text: str or bytes
        :return: Compiled template.
        :rtype: :py:class:`curly.template.Template`
        :raises ValueError: if not possible to compile template.
        """
        return template.Template(self, text)


def env_if(node, env, context):
    """Implementation of ``if`` function call.

    It implements logic of following code:

    .. code-block:: jinja

      {% if last_name %}
          {{ last_name }}
      {% /if %}

    :param curly.parser.Node node: The node with such function call.
    :param Env env: Environment which is used.
    :param dict context: Dictionary with variables for the template.
    :return: Iterator over rendered text chunks
    :rtype: Generator[str]
    """
    return env_predicate(bool, node, env, context)


def env_ifnot(node, env, context):
    """Implementation of ``if-not`` function call.

    It implements logic of following code:

    .. code-block:: jinja

      {% if-not last_name %}
          {{ default_name }}
      {% /if-not %}

    :param curly.parser.Node node: The node with such function call.
    :param Env env: Environment which is used.
    :param dict context: Dictionary with variables for the template.
    :return: Iterator over rendered text chunks
    :rtype: Generator[str]
    """
    return env_predicate(lambda item: not bool(item), node, env, context)


def env_predicate(predicate, node, env, context):
    """Generic implementation of ``if`` and ``if-not`` function calls.

    :param callable predicate: Function which returns ``True`` if
        it is required to render contents of the tag.
    :param curly.parser.Node node: The node with such function call.
    :param Env env: Environment which is used.
    :param dict context: Dictionary with variables for the template.
    :return: Iterator over rendered text chunks
    :rtype: Generator[str]
    """
    value = subprocess.list2cmdline(node.expression)
    resolved = utils.resolve_variable(value, context)

    if predicate(resolved):
        for subnode in node.nodes:
            yield from subnode.emit(env, context)
    else:
        yield ""


def env_loop(node, env, context):
    """Implementation of ``loop`` function call.

    It implements logic of following code:

    .. code-block:: jinja

      {% loop items %}
          - {{ item }}
      {% /loop %}

    If expression is dict, then it will be traversed in sorted order and
    ``item`` is a mapping like ``{"key": k, "value": v}``. Otherwise
    ``item`` is just an item from iterable.

    :param curly.parser.Node node: The node with such function call.
    :param Env env: Environment which is used.
    :param dict context: Dictionary with variables for the template.
    :return: Iterator over rendered text chunks
    :rtype: Generator[str]
    """
    value = subprocess.list2cmdline(node.expression)
    resolved = utils.resolve_variable(value, context)

    context_copy = context.copy()
    if isinstance(resolved, dict):
        for key, value in sorted(resolved.items()):
            context_copy["item"] = {"key": key, "value": value}
            for subnode in node.nodes:
                yield from subnode.emit(env, context_copy)
    else:
        for item in resolved:
            context_copy["item"] = item
            for subnode in node.nodes:
                yield from subnode.emit(env, context_copy)


DEFAULT_ENV = Env()
"""Instance of :py:class:`Env` with default set of functions."""
