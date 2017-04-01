# -*- coding: utf-8 -*-


from curly.template import Template  # NOQA
from curly.env import Env  # NOQA
from curly.env import DEFAULT_ENV  # NOQA


def render(text, context):
    return DEFAULT_ENV.template(text).render(context)
