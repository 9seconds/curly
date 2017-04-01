#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import json
import sys

import curly


def main():
    options = get_options()
    template = options.template.read()

    try:
        print(curly.render(template, options.context), end="")
    except ValueError as exc:
        sys.exit(exc)


def get_options():
    parser = argparse.ArgumentParser(
        description="Render template using curly.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "context",
        default="{}",  # NOQA
        type=json_parameter,
        help="JSON with template context.",
        nargs=argparse.OPTIONAL
    )
    parser.add_argument(
        "template",
        type=argparse.FileType("r", encoding="utf-8"),
        default="-",
        help="File where template is placed. Use '-' for reading from stdin ",
        nargs=argparse.OPTIONAL
    )

    return parser.parse_args()


def json_parameter(value):
    try:
        return json.loads(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Should be JSON: {0}".format(exc)) from exc


if __name__ == "__main__":
    main()
