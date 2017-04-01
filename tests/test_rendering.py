# -*- coding: utf-8 -*-


import itertools

import pytest

from curly import render


@pytest.mark.parametrize("tpl", (
    "",
    "hello",
    "hello {",
    "hello {{",
    "{% {? {{ {{ lala }"
))
def test_nothing_to_do(tpl):
    assert render(tpl, {}) == tpl


def test_print_tag():
    tpl = "Hello {{ name }} {{ title }}{{name}} {{\n\ntitle\n}}"
    assert render(tpl, {"name": "NAME", "title": "TT"}) == \
        "Hello NAME TTNAME TT"


def test_if_tag():
    tpl = "Hello {? qq?}QQ{?} {?pp?}PP{?} Hello"
    assert render(tpl, {"qq": False, "pp": True}) == "Hello  PP Hello"


def test_for_loop_list():
    tpl = "H {% items %}={{ item }}{%} H"
    assert render(tpl, {"items": [1, 2, 3]}) == "H =1=2=3 H"


def test_for_loop_dict():
    tpl = "H {% items%}{{ item.key }}={{ item.value }},{%} H"
    assert render(tpl, {"items": {"b": 2, "a": 1}}) == \
        "H a=1,b=2, H"


def test_for_loop_if():
    tpl = "H {% items %}{?item?}={{item}}={?}{%} H"
    assert render(tpl, {"items": [True, False, 1, 0]}) == \
        "H =True==1= H"


@pytest.mark.parametrize("tagname", "?%")
def test_cannot_find_end_statement(tagname):
    tpl = "H {" + tagname + " var " + tagname + "} H"
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


@pytest.mark.parametrize("tagname", "?%")
def test_cannot_find_start_statement(tagname):
    tpl = "H {%s} H" % tagname
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


@pytest.mark.parametrize("one, another", list(itertools.permutations("?%", 2)))
def test_mixed_statements(one, another):
    tpl = "H {" + one + " var " + one + ("}{%s} {" % another) + \
        "} {%s} H" % one
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


def test_literal_replacement():
    tpl = r"\{\{"
    assert render(tpl, {}) == "{{"
