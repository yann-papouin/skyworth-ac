#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import logging
import math

from enum import IntEnum
from pprint import pformat

from crcmod.predefined import mkPredefinedCrcFun
from .ac_data import AirConditionerData
from .convert import (
    byte2sbyte,
    sbyte2byte,
    barray2blist,
    barray2hexlist,
    barray2sblist,
)

_logger = logging.getLogger(__name__)


class Query(IntEnum):
    TYPE_COMMAND = 0xa1  # -95=161
    TYPE_GET_INFO = 0xa2  # -94=162


class Command:
    POWER = 0xf7
    LIGHT = 0x80
    WIND_LEFT_RIGHT = 0x0f
    WIND_UP_DOWN = 0xf0
    TURBO = 0x80
    MODE = 0xf8
    FAN_SPEED = 0x8f
    TEMPERATURE_SET = 0xe0
    MUTE = 0xbf
    AUXILIARY_HEATING = 0xef
    SLEEP = 0xfd
    ENERGY_SAVING = 0xfe
    TEMPERATURE_MODE = 0xdf
    FILTER_PM25 = 0xbf


def invert(cmd: Command) -> Command:
    if cmd != 128:
        res = 255 - cmd
    else:
        res = cmd
    return res


class Mode(IntEnum):
    AUTO = 0x00
    COOL = 0x01
    DEHUMIDIFIER = 0x02
    FAN = 0x03
    HEAT = 0x04


class Datagram:
    HEADER = 0x7a  # 122
    # ===========================
    DST_ADDRESS = 0x21  # 33 # ?
    SRC_ADDRESS = 0xd5  # 43 # ?
    WIFI_ADDRESS = 0xa2  # -47=209
    AC_ID1 = 0  # ? Not used
    AC_ID2 = 0  # ? Not used
    # ===========================
    AC_DATA0 = 0x0a  # 10 ?
    AC_DATA1 = 0x0a  # 10 ?


RAW_MIN = 0
RAW_MAX = 31


def ensure_raw_range(value: int) -> int:
    if value < RAW_MIN:
        value = RAW_MIN
    elif value > RAW_MAX:
        value = RAW_MAX
    return value


def raw_to_fahrenheit(value: int) -> int:
    # Cannot use standard formula since the ac has
    #  its own table: raw_to_celcius(value) * 1.8 + 32

    FAHRENHEIT_TABLE = {
        0: 61,
        1: 62,
        2: 64,
        3: 66,
        4: 68,
        5: 69,
        6: 71,
        7: 73,
        8: 75,
        9: 77,
        10: 78,
        11: 80,
        12: 82,
        13: 84,
        14: 86,
        15: 87,
        16: 61,
        17: 63,
        18: 65,
        19: 67,
        20: 68,
        21: 70,
        22: 72,
        23: 74,
        24: 76,
        25: 77,
        26: 79,
        27: 81,
        28: 83,
        29: 85,
        30: 86,
        31: 88
    }

    if value in FAHRENHEIT_TABLE:
        res = FAHRENHEIT_TABLE[value]
    else:
        res = 61

    return res


def fahrenheit_to_raw(value: int) -> int:
    raise NotImplemented


def celcius_to_raw(value: int) -> int:
    res = value - 16
    res = ensure_raw_range(res)
    return res


def raw_to_celcius(value: int) -> int:
    return value + 16


modbus_crc = mkPredefinedCrcFun('modbus')


class AirConditionerController:
    def __init__(self, host: str, port: int = 1998) -> None:
        self.host = host
        self.port = port
        self.data = AirConditionerData()
        self._reset_data()

    def _reset_data(self):
        self.data.d1 = 0
        self.data.d2 = 0
        self.data.d3 = 0
        self.data.d4 = sbyte2byte(-124)
        self.data.d5 = 0
        self.data.d6 = 0
        self.data.d7 = 0
        self.data.d8 = 0
        self.data.d9 = 0
        self.data.d10 = 0
        self.data.d13 = 0
        self.data.d14 = 0

    def _get_power(self) -> bool:
        res = (self.data.d1 & invert(Command.POWER)) >> 3
        res = res % 255
        return True if res == 1 else False

    def _set_power(self, state: bool):
        if state:
            self.data.d1 |= Command.POWER
        else:
            self.data.d1 &= ~Command.POWER

    def _get_turbo(self) -> bool:
        res = (self.data.d1 & invert(Command.TURBO)) >> 7
        res = res % 255
        return True if res == 1 else False

    def _set_turbo(self, state: bool):
        # Also called super mode
        if state:
            self.data.d1 |= Command.TURBO
        else:
            self.data.d1 &= ~Command.TURBO

    def _get_mode(self):
        res = (self.data.d1 & invert(Command.MODE)) >> 0
        return res % 255

    def _set_mode(self, value: int):
        controlbit = (value << 0) % 255
        self.data.d1 = (self.data.d1 & Command.MODE) | controlbit

    def _set_swing_off(self):
        self.data.d3 = 0

    def _get_swing_left_right(self) -> int:
        res = (self.data.d3 & invert(Command.WIND_LEFT_RIGHT)) >> 4
        res = res % 255
        return True if res == 1 else False

    def _set_swing_left_right(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 4) % 255
        self.data.d3 = (self.data.d3 & Command.WIND_LEFT_RIGHT) | controlbit

    def _get_swing_up_down(self) -> int:
        res = (self.data.d3 & invert(Command.WIND_UP_DOWN)) >> 0
        res = res % 255
        return True if res == 1 else False

    def _set_swing_up_down(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 0) % 255
        self.data.d3 = (self.data.d3 & Command.WIND_UP_DOWN) | controlbit

    def _get_fan_speed(self) -> int:
        res = (self.data.d1 & invert(Command.FAN_SPEED)) >> 4
        value = res % 255
        return value

    def _set_fan_speed(self, value: int):
        assert (value <= 6)
        controlbit = (value << 4) % 255
        self.data.d1 = (self.data.d1 & Command.FAN_SPEED) | controlbit

    def _set_temperature_set(self, temperature: int):
        if self._get_temperature_mode():
            value = fahrenheit_to_raw(temperature)
        else:
            value = celcius_to_raw(temperature)
        self.data.d2 = (self.data.d2 & Command.TEMPERATURE_SET) | value

    def _get_temperature_set(self) -> int:
        value = self.data.d2 & invert(Command.TEMPERATURE_SET)
        if self._get_temperature_mode():
            temperature = raw_to_fahrenheit(value)
        else:
            temperature = raw_to_celcius(value)
        return temperature

    def _get_mute(self) -> bool:
        res = (self.data.d2 & invert(Command.MUTE)) >> 6
        res = res % 255
        return True if res == 1 else False

    def _set_mute(self, state: bool):
        if state:
            self.data.d2 |= Command.MUTE
        else:
            self.data.d2 &= ~Command.MUTE

    def _get_temperature_mode(self) -> bool:
        res = (self.data.d2 & invert(Command.TEMPERATURE_MODE)) >> 5
        res = res % 255
        return True if res == 1 else False

    def _set_temperature_mode(self, state: bool):
        """ Change Temperature mode to Celsius/Fahrenheit
        Args:
            state (bool): 
                if True: Celsius to Fahrenheit
                if False: Fahrenheit to Celsius
        """
        control = 1 if state else 0
        controlbit = (control << 5) % 255
        self.data.d2 = (self.data.d2 & Command.TEMPERATURE_MODE) | controlbit
        _logger.debug(self.data.d2)

    def _get_auxiliary_heating(self) -> bool:
        res = (self.data.d4 & invert(Command.AUXILIARY_HEATING)) >> 4
        res = res % 255
        return True if res == 1 else False

    def _set_auxiliary_heating(self, state: bool):
        if state:
            self.data.d4 |= Command.AUXILIARY_HEATING
        else:
            self.data.d4 &= ~Command.AUXILIARY_HEATING

    def _get_sleep(self) -> bool:
        res = (self.data.d4 & invert(Command.SLEEP)) >> 1
        res = res % 255
        return True if res == 1 else False

    def _set_sleep(self, state: bool):
        if state:
            self.data.d4 |= Command.SLEEP
        else:
            self.data.d4 &= ~Command.SLEEP

    def _get_energy_saving(self) -> bool:
        res = (self.data.d4 & invert(Command.ENERGY_SAVING)) >> 0
        res = res % 255
        return True if res == 1 else False

    def _set_energy_saving(self, state: bool):
        control = 1 if state else 0
        if control:
            self.data.d4 |= Command.ENERGY_SAVING
        else:
            self.data.d4 &= ~Command.ENERGY_SAVING

    def _get_filter(self) -> bool:
        res = (self.data.d4 & invert(Command.FILTER_PM25)) >> 6
        res = res % 255
        return True if res == 1 else False

    def _set_filter(self, state: bool):
        if state:
            self.data.d4 |= Command.FILTER_PM25
        else:
            self.data.d4 &= ~Command.FILTER_PM25

    def _get_light(self) -> bool:
        res = (self.data.d4 & invert(Command.LIGHT)) >> 7
        res = res % 255
        return True if res == 1 else False

    def _set_light(self, state: bool):
        if state:
            self.data.d4 |= Command.LIGHT
        else:
            self.data.d4 &= ~Command.LIGHT

    def _get_state(self):
        res = {
            'auxiliary_heating': self._get_auxiliary_heating(),
            'temperature_mode': self._get_temperature_mode(),
            'temperature_set': self._get_temperature_set(),
            'swing_left_right': self._get_swing_left_right(),
            'swing_up_down': self._get_swing_up_down(),
            'energy_saving': self._get_energy_saving(),
            'fan_speed': self._get_fan_speed(),
            'filter': self._get_filter(),
            'light': self._get_light(),
            'mode': self._get_mode(),
            'mute': self._get_mute(),
            'power': self._get_power(),
            'sleep': self._get_sleep(),
            'turbo': self._get_turbo(),
        }
        _logger.info(pformat(res))
        return res

    def _run_command(self):
        _logger.info('_run_command')
        data = [
            self.data.d13, self.data.d14, self.data.d1, self.data.d2, self.data.d3,
            self.data.d4, self.data.d5, self.data.d6, self.data.d7, self.data.d8,
            self.data.d9, self.data.d10
        ]
        self._send(Query.TYPE_COMMAND, data)

    def _run_get_info(self):
        _logger.info('_run_get_info')
        data = self._send(Query.TYPE_GET_INFO)
        if len(data) >= 2 and (data[0] == data[1] == Datagram.HEADER):
            # _logger.info('Header is correct')
            # Split data array to get only valid data for one side
            # and crc data only for yhe other side
            data_crc_array = data[-2:]
            data_without_crc = data[:-2]
            # Regenerate CRC from our side
            crc16 = modbus_crc(bytearray(data_without_crc))
            computed_crc_array = [
                (crc16 >> 8) & 0xff,
                crc16 & 0xff,
            ]
            # Check if CRC matches:
            if data_crc_array == computed_crc_array:
                # _logger.info('CRC is correct')
                protocol_version = data[8]
                aircondition_motherboard_version = data[9]
                rec_cmd = data[7]
                wifi_cmd = data[10]

                # _logger.info(f'protocol_version={protocol_version}')
                # _logger.info(
                #     f'aircondition_motherboard_version={aircondition_motherboard_version}'
                # )
                # _logger.info(f'rec_cmd={rec_cmd}')
                # _logger.info(f'wifi_cmd={wifi_cmd}')

                if data[3] == Datagram.DST_ADDRESS:
                    inner_temperature = data[10]
                    inner_temperature_float = data[11]
                    _logger.info(f'inner_temperature={inner_temperature}')
                    _logger.info(
                        f'inner_temperature_float={inner_temperature_float}'
                    )

                    self.data.d1 = data[13]
                    self.data.d2 = data[14]
                    self.data.d3 = data[15]
                    self.data.d4 = data[16] & 254
                    self.data.d5 = data[17]
                    self.data.d6 = data[18]
                    self.data.d7 = data[19]
                    self.data.d8 = data[20]
                    self.data.d9 = data[21]
                    self.data.d10 = data[22]

                    fan = ((data[13] & 112) >> 4)
                    print(fan)

                    # self._save_swing_state()
                    # self._save_fan_speed()
                elif data[3] == Datagram.WIFI_ADDRESS:
                    pass

            else:
                _logger.error('Invalid CRC')

    def _send(self, type: Query, data=[]) -> list:
        """Build datagram with message data

        Args:
            type (Query): Get or Set data
            data (list, optional): [description]. Defaults to [].

        Returns:
            list: [description]
        """
        BASE_LENGTH = 0x0a  # 10
        CRC_LENGTH = 0x02  # 2
        LENGTH = BASE_LENGTH + len(data) + CRC_LENGTH

        raw_message = [
            Datagram.HEADER, Datagram.HEADER, Datagram.DST_ADDRESS,
            Datagram.SRC_ADDRESS, LENGTH, Datagram.AC_ID1, Datagram.AC_ID2,
            int(type), Datagram.AC_DATA0, Datagram.AC_DATA1
        ] + data

        crc16 = modbus_crc(bytearray(raw_message))
        crc_array = [
            (crc16 >> 8) & 0xff,
            crc16 & 0xff,
        ]

        raw_message += crc_array
        return self._raw_send(raw_message)

    def _raw_send(self, message: list) -> list:
        BUFFER_SIZE = 1024

        raw_message = bytearray(message)
        _logger.debug("data >> %s", barray2hexlist(raw_message))
        _logger.debug("data >> %s", barray2sblist(raw_message))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(raw_message)
        raw_data = s.recv(BUFFER_SIZE)
        s.close()

        _logger.debug("data << %s", barray2hexlist(raw_data))
        _logger.debug("data << %s", barray2sblist(raw_data))

        data = barray2blist(raw_data)
        return data
