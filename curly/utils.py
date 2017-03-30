# -*- coding: utf-8 -*-


import re
import textwrap


def make_regexp(pattern):
    return re.compile(textwrap.dedent(pattern), re.VERBOSE)


def resolve_variable(varname, context):
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
