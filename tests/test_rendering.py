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
    tpl = "Hello {% if qq %}QQ{%/if%} {%if   pp  %}PP{% /if%} Hello"
    assert render(tpl, {"qq": False, "pp": True}) == "Hello  PP Hello"


def test_elif_tag():
    tpl = "Hello {% if qq %}1{%elif pp%}2{%else%}3{%/if%}"
    assert render(tpl, {"qq": False, "pp": True}) == "Hello 2"


def test_else_tag():
    tpl = "Hello {% if qq %}1{%elif pp%}2{%else%}3{%/if%}"
    assert render(tpl, {"qq": False, "pp": False}) == "Hello 3"


def test_double_else_tag():
    tpl = "Hello {% if qq %}1{%else%}3{%elif pp%}2{%else%}3{%/if%}"
    with pytest.raises(ValueError):
        render(tpl, {"qq": False, "pp": False})


def test_double_else_end_tag():
    tpl = "Hello {% if qq %}13{%elif pp%}2{%else%}3{%else%}4{%/if%}"
    with pytest.raises(ValueError):
        render(tpl, {"qq": False, "pp": False})


def test_for_loop_list():
    tpl = "H {% loop items %}={{ item }}{% /loop %} H"
    assert render(tpl, {"items": [1, 2, 3]}) == "H =1=2=3 H"


def test_for_loop_dict():
    tpl = "H {% loop items%}{{ item.key }}={{ item.value }},{% /loop %} H"
    assert render(tpl, {"items": {"b": 2, "a": 1}}) == \
        "H a=1,b=2, H"


def test_for_loop_if():
    tpl = "H {% loop items %}{% if item %}={{item}}={% /if %}{% /loop %} H"
    assert render(tpl, {"items": [True, False, 1, 0]}) == \
        "H =True==1= H"


@pytest.mark.parametrize("tagname", ["loop", "if", "elif", "else"])
def test_cannot_find_end_statement(tagname):
    tpl = "H {%% %s condition %%}" % tagname
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


@pytest.mark.parametrize("tagname", ["loop", "if", "elif", "else"])
def test_cannot_find_start_statement(tagname):
    tpl = "H {%% /%s %%} H" % tagname
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


@pytest.mark.parametrize(
    "one, another", list(itertools.permutations(
        ["loop", "if", "elif", "else"], 2)))
def test_mixed_statements(one, another):
    tpl = "H {%% %s %%} {%% / %s %%}" % (one, another)
    with pytest.raises(ValueError):
        render(tpl, {"var": 1})


def test_literal_replacement():
    tpl = r"\{\{"
    assert render(tpl, {}) == "{{"
