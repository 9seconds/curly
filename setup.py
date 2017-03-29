#!/usr/bin/env python
# -*- coding: utf-8 -*-


import setuptools


def get_description():
    return ""
    # with open("README.rst", "r") as description_fp:
    #     return description_fp.read().strip()


setuptools.setup(
    name="curly",
    version="0.0.1",
    author="Sergey Arkhipov",
    author_email="nineseconds@yandex.ru",
    maintainer="Sergey Arkhipov",
    maintainer_email="nineseconds@yandex.ru",
    license="MIT",
    description="A minimal template engine",
    long_description=get_description(),
    packages=[
        "curly"
    ],
    install_requires=[]
)
