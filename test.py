#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.DEBUG)


# Clear console
def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def byte2sbyte(value):
    if value > 127:
        return (256 - value) * (-1)
    else:
        return value


def invert(cmd):
    if cmd != 128:
        res = 255 - cmd
    else:
        res = cmd
    return res


def _debug_value(property_name, value, symbol='->'):
    _logger.info(
        '%s %s byte= %3d  signed-byte= % 4d  hex=0x%02x  binary=%s',
        property_name,
        symbol,
        value,
        byte2sbyte(value),
        value,
        format(value, '#010b'),
    )


def _set_bit(value, state: bool, mask):
    init_value = value

    if state:
        value |= mask
    else:
        value &= ~mask

    # _logger.info(
    #     '        set %s : %d -> %d MASK=[0x%x] %s', state, init_value, value, mask,
    #     format(mask, '#010b')
    # )
    return value


MUTE = 0xbf
POWER = 0xf7
LIGHT = 0x80
WIND_LEFT_RIGHT = 0x0f
WIND_UP_DOWN = 0xf0
TURBO = 0x80
MODE = 0xf8

mask_to_test = [
    ('MUTE', MUTE),
    ('LIGHT', LIGHT),
    ('POWER', POWER),
]
to_invert = [False, True]

clear()
for name, mask in mask_to_test:
    for need_invert in to_invert:
        if need_invert:
            mask = invert(mask)

        mask_help = 'MASK=[0x%x] %s' % (mask, format(mask, '#010b'))
        print('\n====', name, mask_help, '==== INVERT =', need_invert)

        A = 0
        _debug_value('A', A)
        A = _set_bit(A, True, mask)
        _debug_value('A', A)
        A = _set_bit(A, False, mask)
        _debug_value('A', A)

        print('---')

        A = 255
        _debug_value('A', A)
        A = _set_bit(A, True, mask)
        _debug_value('A', A)
        A = _set_bit(A, False, mask)
        _debug_value('A', A)
