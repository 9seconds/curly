# -*- coding: utf-8 -*-
"""A various utilities which are used by Curly."""


import re
import shlex
import textwrap


def make_regexp(pattern):
    """Make regular expression from the given patterns.

    This is just a trivial wrapper for :py:func:`re.compile` which sets
    a list of default flags.

    :param str pattern: A pattern to compile into regular expression.
    :return: Compiled regular expression
    """
    pattern = textwrap.dedent(pattern)
    pattern = re.compile(pattern, re.MULTILINE | re.VERBOSE | re.DOTALL)

    return pattern


def make_expression(text):
    """Make template expression from the tag in the pattern.

    Anatomy of the tag is rather simple: ``{% if something | went
    | through "named pipe" %}`` is a valid tag. ``if`` here is the
    function name you are going to apply. And this long line ``something
    | went | through "named pipe"`` is called expression. Yes, basic
    reference implementation considers whole expression as a name in the
    context, but in more advanced implementations, it is a DSL which is
    used for calculation of function arguments from the expression.

    This function uses shell lexing to split expression above into
    the list of words like ``["something", "|", "went", "through", "named
    pipe"]``.

    :param text: A text to make expression from
    :type text: str or None
    :return: The list of parsed expressions
    :rtype: list[str]
    """
    text = text or ""
    text = text.strip()
    text = shlex.split(text)
    if not text:
        text = [""]

    return text


def resolve_variable(varname, context):
    """Resolve value named as varname from the context.

    In most trivial case, implementation of the method is like that:

    .. code-block:: python3

      def resolve_variable(varname, context):
          return context[varname]

    but it works only for the most trivial cases. Even such simple
    template language as Curly is is required to support dot notation.
    So:

    .. code-block:: pycon

      >>> context = {
      ...     "first_name": "Sergey",
      ...     "last_name": "Arkhipov",
      ...     "roles": {
      ...         "admin": [
      ...             "view_user",
      ...             "update_user",
      ...             "delete_user"
      ...         ]
      ...     }
      ... }
      >>> resolve_variable("roles.admin.1", context)
      'update_user'

    So it is possible to resolve nested structures and also - arrays.
    But sometimes you may have ambiguous situations. The rule of this
    function is to try to resolve literally before going deep into the
    nested structure.

    .. code-block:: pycon

      >>> context = {
      ...     "first_name": "Sergey",
      ...     "last_name": "Arkhipov",
      ...     "roles": {
      ...         "admin": [
      ...             "view_user",
      ...             "update_user",
      ...             "delete_user"
      ...         ]
      ...     },
      ...     "roles.admin.1": "haha!"
      ... }
      >>> resolve_variable("roles.admin.1", context)
      'haha!'

    Also, dot notation supports not only items, but attributes also.

    :param str varname: Expression to resolve
    :param dict context: A dictionary with variables to resolve.
    :return: Resolved value
    :raises ValueError: if it is not possible to resolve ``varname``
        within a ``context``.
    """
    try:
        return get_item_or_attr(varname, context)
    except ValueError:
        pass

    chunks = varname.split(".", 1)
    if len(chunks) == 1:
        raise ValueError("Context {0!r} has no key {1!r}".format(
            context, varname))

    current_name, rest_name = chunks
    new_context = resolve_variable(current_name, context)
    resolved = resolve_variable(rest_name, new_context)

    return resolved


def get_item_or_attr(varname, context):
    """Resolve literal varname in context for :py:func:`resolve_variable`.

    Supports resolving of items and attributes. Also, tries indexes if
    possible.

    :param str varname: Expression to resolve
    :param dict context: A dictionary with variables to resolve.
    :return: Resolved value
    :raises ValueError: if it is not possible to resolve ``varname``
        within a ``context``.
    """
    try:
        return context[varname]
    except Exception:
        try:
            return getattr(context, varname)
        except Exception as exc:
            pass

    if isinstance(varname, str) and varname.isdigit():
        return get_item_or_attr(int(varname), context)
    raise ValueError("Cannot extract {0!r} from {1!r}".format(
        varname, context))
