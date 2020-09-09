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
    def _debug_value(cls, property_name, value):
        _logger.debug(
            '%s -> byte=%3d signed-byte=% 4d hex=0x%02x binary=%s',
            property_name,
            value,
            byte2sbyte(value),
            value,
            format(value, '#010b'),
        )

    def get_debug_data(self):
        res = {
            'd13': AirConditionerData._debug_value('d13', self.d13),
            'd14': AirConditionerData._debug_value('d14', self.d14),
            'd1': AirConditionerData._debug_value('d1', self.d1),
            'd2': AirConditionerData._debug_value('d2', self.d2),
            'd3': AirConditionerData._debug_value('d3', self.d3),
            'd4': AirConditionerData._debug_value('d4', self.d4),
            'd5': AirConditionerData._debug_value('d5', self.d5),
            'd6': AirConditionerData._debug_value('d6', self.d6),
            'd7': AirConditionerData._debug_value('d7', self.d7),
            'd8': AirConditionerData._debug_value('d8', self.d8),
            'd9': AirConditionerData._debug_value('d9', self.d9),
            'd10': AirConditionerData._debug_value('d10', self.d10),
        }
        return res

    def _set_byte_value(self, property_name, index, value):
        if self._data[index] != value:
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