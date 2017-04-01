# -*- coding: utf-8 -*-


import subprocess

from curly import template
from curly import utils


class Env:

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

    def __contains__(self, key):
        return key in self.functions

    def get(self, key, default=None):
        if key not in self.functions:
            return default

        return self.functions[key]

    def template(self, text):
        return template.Template(self, text)


def env_if(node, env, context):
    return env_predicate(bool, node, env, context)


def env_ifnot(node, env, context):
    return env_predicate(lambda item: not bool(item), node, env, context)


def env_predicate(predicate, node, env, context):
    value = subprocess.list2cmdline(node.expression)
    resolved = utils.resolve_variable(value, context)

    if predicate(resolved):
        for subnode in node.nodes:
            yield from subnode.emit(env, context)
    else:
        yield ""


def env_loop(node, env, context):
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
