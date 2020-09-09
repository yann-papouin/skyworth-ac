#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from .convert import (
    byte2sbyte,
    sbyte2byte,
    barray2blist,
    barray2hexlist,
    barray2sblist,
)

_logger = logging.getLogger(__name__)


class AirConditionerData:
    def __init__(self) -> None:
        self._data = [0 for x in range(12)]

    @classmethod
    def _debug_value(cls, property_name, value, symbol='->'):
        res = '%s %s byte= %3d  signed-byte= % 4d  hex=0x%02x  binary=%s' % (
            property_name,
            symbol,
            value,
            byte2sbyte(value),
            value,
            format(value, '#010b'),
        )
        # Log to debug only if property_name is set
        if property_name.strip():
            _logger.debug(res)
        return res

    def get_debug_data(self):
        SYMBOL = "==="
        res = {
            'd13': AirConditionerData._debug_value('', self.d13,SYMBOL),
            'd14': AirConditionerData._debug_value('', self.d14,SYMBOL),
            'd1': AirConditionerData._debug_value(' ', self.d1,SYMBOL),
            'd2': AirConditionerData._debug_value(' ', self.d2,SYMBOL),
            'd3': AirConditionerData._debug_value(' ', self.d3,SYMBOL),
            'd4': AirConditionerData._debug_value(' ', self.d4,SYMBOL),
            'd5': AirConditionerData._debug_value(' ', self.d5,SYMBOL),
            'd6': AirConditionerData._debug_value(' ', self.d6,SYMBOL),
            'd7': AirConditionerData._debug_value(' ', self.d7,SYMBOL),
            'd8': AirConditionerData._debug_value(' ', self.d8,SYMBOL),
            'd9': AirConditionerData._debug_value(' ', self.d9,SYMBOL),
            'd10': AirConditionerData._debug_value('', self.d10,SYMBOL),
        }
        return res

    def _set_byte_value(self, property_name, index, value):
        if self._data[index] != value:
            AirConditionerData._debug_value(
                property_name, self._data[index], '=='
            )
            self._data[index] = value
            AirConditionerData._debug_value(property_name, value)

    @property
    def d13(self):
        return self._data[0]

    @d13.setter
    def d13(self, value):
        self._set_byte_value('d13', 0, value)

    @property
    def d14(self):
        return self._data[1]

    @d14.setter
    def d14(self, value):
        self._set_byte_value('d14', 1, value)

    @property
    def d1(self):
        return self._data[2]

    @d1.setter
    def d1(self, value):
        self._set_byte_value('d1', 2, value)

    @property
    def d2(self):
        return self._data[3]

    @d2.setter
    def d2(self, value):
        self._set_byte_value('d2', 3, value)

    @property
    def d3(self):
        return self._data[4]

    @d3.setter
    def d3(self, value):
        self._set_byte_value('d3', 4, value)

    @property
    def d4(self):
        return self._data[5]

    @d4.setter
    def d4(self, value):
        self._set_byte_value('d4', 5, value)

    @property
    def d5(self):
        return self._data[6]

    @d5.setter
    def d5(self, value):
        self._set_byte_value('d5', 6, value)

    @property
    def d6(self):
        return self._data[7]

    @d6.setter
    def d6(self, value):
        self._set_byte_value('d6', 7, value)

    @property
    def d7(self):
        return self._data[8]

    @d7.setter
    def d7(self, value):
        self._set_byte_value('d7', 8, value)

    @property
    def d8(self):
        return self._data[9]

    @d8.setter
    def d8(self, value):
        self._set_byte_value('d8', 9, value)

    @property
    def d9(self):
        return self._data[10]

    @d9.setter
    def d9(self, value):
        self._set_byte_value('d9', 10, value)

    @property
    def d10(self):
        return self._data[11]

    @d10.setter
    def d10(self, value):
        self._set_byte_value('d10', 11, value)


if __name__ == "__main__":
    _logger.addHandler(logging.StreamHandler())
    _logger.setLevel(logging.DEBUG)

    air_conditioner_data = AirConditionerData()
    air_conditioner_data.d1 = 20
    air_conditioner_data.d2 = 9
    air_conditioner_data.d3 = 10
    air_conditioner_data.d5 = 67
    air_conditioner_data.d13 = 0