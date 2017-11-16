# -*- coding: utf-8 -*-

from os import environ


def get_env(variable, *, default=None, convert=None):
    value = environ.get("GOLD_DIGGER_" + variable.upper(), default)

    if value is not None and convert:
        return convert(value)
    else:
        return value
