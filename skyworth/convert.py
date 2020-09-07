#!/usr/bin/env python
# -*- coding: utf-8 -*-


def byte2sbyte(value):
    if value > 127:
        return (256 - value) * (-1)
    else:
        return value


def sbyte2byte(value):
    if value < 0:
        return 256 + value
    else:
        return value


def barray2blist(value):
    return list(value)


def barray2hexlist(value):
    return [hex(x) for x in list(value)]


def barray2sblist(value):
    return [byte2sbyte(x) for x in list(value)]
