# -*- coding: utf-8 -*-


import pytest

from curly import utils


@pytest.mark.parametrize("expression, search, value", (
    (".+", "hello world  ", "hello world  "),
    ("\w+", "привет1 мир", "привет1"),
    ("""
     \w+
     \s
     \w+
     """, "привет мир", "привет мир")
))
def test_make_regexp(expression, search, value):
    regexp = utils.make_regexp(expression)
    assert regexp.match(search).group(0) == value


def test_resolve_variable():
    ctx = {"a": [{"b": 1}, {"c": {"d": "e"}}]}
    assert utils.resolve_variable("a.1.c.d", ctx) == "e"


def test_resolve_first():
    ctx = {"a": {"b": 1}, "a.b": 2}
    assert utils.resolve_variable("a.b", ctx) == 2


def test_cannot_resolve():
    ctx = {"a": {"b": 1}, "a.b": 2}
    with pytest.raises(ValueError):
        utils.resolve_variable("a.c", ctx)
