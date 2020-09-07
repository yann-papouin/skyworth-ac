#!/bin/python

import socket
import logging
from enum import Enum, IntEnum
from pprint import pformat

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Add the handler to the logger
_logger.addHandler(handler)


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


# CRC [ 107, -69]

from crcmod.predefined import mkPredefinedCrcFun
modbus_crc = mkPredefinedCrcFun('modbus')


class Query(IntEnum):
    TYPE_COMMAND = 0xa1  # -95=161
    #TYPE_GET_INFO = 0xa7  # -89=167
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


class ControlAction(IntEnum):
    OFF = 0
    ON = 1


class SwingAction(IntEnum):
    OFF = 0
    LEFT_RIGHT = 1
    UP_DOWN = 2
    ALL = 2


class ModeAction(IntEnum):
    AUTO = 0
    COOL = 1
    HEAT = 2
    DEHUMIDIFIER = 3
    FAN = 4


class SpeedAction(IntEnum):
    AUTO = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SPEED_4 = 4
    SPEED_5 = 5
    SPEED_6 = 6


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


def raw_to_celcius(value: int) -> int:
    return value + 16


class AirConditionner:
    def __init__(self, host: str, port: int = 1998) -> None:
        self.host = host
        self.port = port
        # Used to save and restore swing state per mode
        self._swing_state = {
            ModeAction.AUTO: 0,
            ModeAction.COOL: 0,
            ModeAction.HEAT: 0,
            ModeAction.DEHUMIDIFIER: 0,
            ModeAction.FAN: 0,
        }
        # Used to save and restore fan speed per mode
        self._fan_speed = {
            ModeAction.AUTO: 0,
            ModeAction.COOL: 0,
            ModeAction.HEAT: 0,
            ModeAction.DEHUMIDIFIER: 0,
            ModeAction.FAN: 0,
        }
        # Used to save and restore temperature set (celsius/fahrenheit)
        self._temperature_set = {
            ModeAction.AUTO: 9,  # Always 9 in auto mode
            ModeAction.COOL: 0,
            ModeAction.HEAT: 0,
            ModeAction.DEHUMIDIFIER: 0,
            ModeAction.FAN: 0,
        }
        self._reset_data()

    def _reset_data(self):
        self.data1 = 0
        self.data2 = 0
        self.data3 = 0
        self.data4 = sbyte2byte(-124)
        self.data5 = 0
        self.data6 = 0
        self.data7 = 0
        self.data8 = 0
        self.data9 = 0
        self.data10 = 0
        self.data13 = 0
        self.data14 = 0

    def _get_mode_from_state(self) -> ModeAction:
        mode = self._get_mode()
        if mode == Mode.AUTO:
            res = ModeAction.AUTO
        elif mode == Mode.COOL:
            res = ModeAction.COOL
        elif mode == Mode.HEAT:
            res = ModeAction.HEAT
        elif mode == Mode.DEHUMIDIFIER:
            res = ModeAction.DEHUMIDIFIER
        elif mode == Mode.FAN:
            res = ModeAction.FAN
        else:
            _logger.error('Invalid mode %d', mode)
            res = ModeAction.AUTO
        return res

    def _get_power(self) -> bool:
        res = (self.data1 & invert(Command.POWER)) >> 3
        res = res % 255
        return True if res == 1 else False

    def _set_power(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 3) % 255
        self.data1 = (self.data1 & Command.POWER) | controlbit

    def _get_turbo(self) -> bool:
        res = (self.data1 & invert(Command.TURBO)) >> 7
        res = res % 255
        return True if res == 1 else False

    def _set_turbo(self, state: bool):
        # Also called super mode
        control = 1 if state else 0
        controlbit = (control << 7) % 255
        self.data1 = (self.data1 & Command.TURBO) | controlbit

    def _get_mode(self):
        res = (self.data1 & invert(Command.MODE)) >> 0
        return res % 255

    def _set_mode(self, value: int):
        controlbit = (value << 0) % 255
        self.data1 = (self.data1 & Command.MODE) | controlbit

    def _set_swing_off(self):
        self.data3 = 0

    def _get_swing_left_right(self) -> int:
        res = (self.data3 & invert(Command.WIND_LEFT_RIGHT)) >> 4
        res = res % 255
        return True if res == 1 else False

    def _set_swing_left_right(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 4) % 255
        self.data3 = (self.data3 & Command.WIND_LEFT_RIGHT) | controlbit

    def _get_swing_up_down(self) -> int:
        res = (self.data3 & invert(Command.WIND_UP_DOWN)) >> 0
        res = res % 255
        return True if res == 1 else False

    def _set_swing_up_down(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 0) % 255
        self.data3 = (self.data3 & Command.WIND_UP_DOWN) | controlbit

    def _get_fan_speed(self) -> int:
        res = (self.data1 & invert(Command.FAN_SPEED)) >> 4
        value = res % 255
        return value

    def _set_fan_speed(self, value: int):
        assert (value <= 6)
        controlbit = (value << 4) % 255
        self.data1 = (self.data1 & Command.FAN_SPEED) | controlbit
        self._save_fan_speed()

    def _save_swing_state(self):
        # saveWindDirection
        current_mode = self._get_mode_from_state()
        self._swing_state[current_mode] = self.data3
        _logger.debug(
            "Swing state for %s saved to %d",
            current_mode,
            self._swing_state[current_mode],
        )

    def _restore_swing_state(self):
        # remember____WindDirection
        current_mode = self._get_mode_from_state()
        self.data3 = self._swing_state[current_mode]
        pass

    def _save_fan_speed(self):
        # saveWindSpeed
        current_mode = self._get_mode_from_state()
        self._fan_speed[current_mode] = self._get_fan_speed()
        _logger.debug(
            "Fan speed for %s saved to %d",
            current_mode,
            self._fan_speed[current_mode],
        )

    def _restore_fan_speed(self):
        # remember____WindSpeed
        current_mode = self._get_mode_from_state()
        speed = self._fan_speed[current_mode]
        _logger.debug(
            "Restore fan speed for %s to %d",
            current_mode,
            self._swing_state[current_mode],
        )
        self._set_fan_speed(speed)

    def _save_temperature_set(self):
        current_mode = self._get_mode_from_state()
        self._temperature_set[current_mode] = 0

    def _restore_temperature_set(self):
        # Check for getFahrenheitByte in original implementation
        current_mode = self._get_mode_from_state()
        temperature = self._temperature_set[current_mode]
        self._set_temperature_set(temperature)

    def _set_temperature_set(self, temperature: int):
        self.data2 = (self.data2 & Command.TEMPERATURE_SET) | temperature

    def _get_temperature_set(self) -> int:
        value = self.data2 & invert(Command.TEMPERATURE_SET)
        if self._get_temperature_mode():
            temperature = raw_to_fahrenheit(value)
        else:
            temperature = raw_to_celcius(value)
        return temperature

    def _get_mute(self) -> bool:
        res = (self.data2 & invert(Command.MUTE)) >> 6
        res = res % 255
        return True if res == 1 else False

    def _set_mute(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 6) % 255
        self.data2 = (self.data2 & Command.MUTE) | controlbit

    def _get_temperature_mode(self) -> bool:
        res = (self.data2 & invert(Command.TEMPERATURE_MODE)) >> 5
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
        self.data2 = (self.data2 & Command.TEMPERATURE_MODE) | controlbit

    def _get_auxiliary_heating(self) -> bool:
        res = (self.data4 & invert(Command.AUXILIARY_HEATING)) >> 4
        res = res % 255
        return True if res == 1 else False

    def _set_auxiliary_heating(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 4) % 255
        self.data4 = (self.data4 & Command.AUXILIARY_HEATING) | controlbit

    def _get_sleep(self) -> bool:
        res = (self.data4 & invert(Command.SLEEP)) >> 1
        res = res % 255
        return True if res == 1 else False

    def _set_sleep(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 1) % 255
        self.data4 = (self.data4 & Command.SLEEP) | controlbit

    def _get_energy_saving(self) -> bool:
        res = (self.data4 & invert(Command.ENERGY_SAVING)) >> 0
        res = res % 255
        return True if res == 1 else False

    def _set_energy_saving(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 0) % 255
        self.data4 = (self.data4 & Command.ENERGY_SAVING) | controlbit

    def _get_filter(self) -> bool:
        res = (self.data4 & invert(Command.FILTER_PM25)) >> 6
        res = res % 255
        return True if res == 1 else False

    def _set_filter(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 6) % 255
        self.data4 = (self.data4 & Command.FILTER_PM25) | controlbit

    def _get_light(self) -> bool:
        res = (self.data4 & invert(Command.LIGHT)) >> 7
        res = res % 255
        return True if res == 1 else False

    def _set_light(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 7) % 255
        self.data4 = (self.data4 & Command.LIGHT) | controlbit

    def _get_state(self):
        res = {
            'auxiliary_heating': self._get_auxiliary_heating(),
            'temperature_mode': self._get_temperature_mode(),
            'temperature_set': self._get_temperature_set(),
            'mode_from_state': self._get_mode_from_state(),
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

    def power_on(self):
        self._set_power(True)
        self._run_command()

    def power_off(self):
        self._set_power(False)
        self._run_command()

    def swing_get(self) -> SwingAction:
        lr = self._get_swing_left_right()
        ud = self._get_swing_up_down()
        if lr and ud:
            res = SwingAction.ALL
        elif lr and not ud:
            res = SwingAction.LEFT_RIGHT
        elif not lr and ud:
            res = SwingAction.UP_DOWN
        else:
            res = SwingAction.OFF
        return res

    def swing_set(self, action: SwingAction):
        self._set_power(True)
        if action == SwingAction.OFF:
            self._set_swing_off()
        elif action == SwingAction.LEFT_RIGHT:
            self._set_swing_left_right(True)
            self._set_swing_up_down(False)
        elif action == SwingAction.UP_DOWN:
            self._set_swing_up_down(True)
            self._set_swing_left_right(False)
        elif action == SwingAction.ALL:
            self._set_swing_up_down(True)
            self._set_swing_left_right(True)
        self._save_swing_state()

    def mode_set(self, action: ModeAction):
        self._set_power(True)
        if action == ModeAction.AUTO:
            self._set_power(True)
            self._set_turbo(False)
            self._set_mode(Mode.AUTO)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.COOL:
            self._set_power(True)
            self._set_mode(Mode.COOL)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.HEAT:
            self._set_power(True)
            self._set_mode(Mode.HEAT)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(True)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.DEHUMIDIFIER:
            self._set_power(True)
            self._set_mode(Mode.DEHUMIDIFIER)
            self._set_turbo(False)
            self._set_fan_speed(1)
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.FAN:
            self._set_power(True)
            self._set_mode(Mode.FAN)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        else:
            raise Exception("Unknown ModeAction")
        self._run_command()

    def speed_set(self, speed: SpeedAction):
        self._set_power(True)
        self._set_turbo(False)
        self._set_mute(False)
        self._set_fan_speed(speed)
        self._run_command()

    def sleep_set(self, state: bool):
        current_mode = self._get_mode_from_state()
        self._set_power(True)

        if current_mode not in (ModeAction.AUTO, ModeAction.FAN):
            self._set_sleep(state)
            # TODO: Check if condition is ok
            if not state:
                self._set_energy_saving(False)
        else:
            self._set_sleep(False)
        self._run_command()

    def filter_set(self, state: bool):
        self._set_power(True)
        self._set_filter(state)
        self._run_command()

    def light_on(self):
        self._set_light(True)
        self._run_command()

    def light_off(self):
        self._set_light(False)
        self._run_command()

    def temperature_mode_F2C(self):
        self._set_temperature_mode(False)
        self._run_command()

    def temperature_mode_C2F(self):
        self._set_temperature_mode(True)
        self._run_command()

    def _run_command(self, command: Command):
        data = [
            self.data13, self.data14, self.data1, self.data2, self.data3,
            self.data4, self.data5, self.data6, self.data7, self.data8,
            self.data9, self.data10
        ]
        self._send(Query.TYPE_COMMAND, data)

    def _run_get_info(self):
        data = self._send(Query.TYPE_GET_INFO)
        if len(data) >= 2 and (data[0] == data[1] == Datagram.HEADER):
            _logger.info('Header is correct')
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
                _logger.info('CRC is correct')
                protocol_version = data[8]
                aircondition_motherboard_version = data[9]
                rec_cmd = data[7]
                wifi_cmd = data[10]

                _logger.info(f'protocol_version={protocol_version}')
                _logger.info(
                    f'aircondition_motherboard_version={aircondition_motherboard_version}'
                )
                _logger.info(f'rec_cmd={rec_cmd}')
                _logger.info(f'wifi_cmd={wifi_cmd}')

                if data[3] == Datagram.DST_ADDRESS:
                    inner_temperature = data[10]
                    inner_temperature_float = data[11]
                    _logger.info(f'inner_temperature={inner_temperature}')
                    _logger.info(
                        f'inner_temperature_float={inner_temperature_float}'
                    )

                    self.data1 = data[13]
                    self.data2 = data[14]
                    self.data3 = data[15]
                    self.data4 = data[16] & 254
                    self.data5 = data[17]
                    self.data6 = data[18]
                    self.data7 = data[19]
                    self.data8 = data[20]
                    self.data9 = data[21]
                    self.data10 = data[22]

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


# MESSAGE:       [122, 122, 33, -43, 24, 0, 0, -95, 10, 10, 0, 0, 4, 72, 0, 0, 0, 0, 0, 0, 0, 0, 107, -69]
# received data: [122, 122, -43, 33, 28, 0, 0, -93, 10, 10, 24, 5, 0, 4, 72, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -13, -26]

# import time
# ac = AirConditionner('192.168.10.22')
# ac.light_on()
# time.sleep(1)
# ac.light_off()
# time.sleep(1)

ac = AirConditionner('192.168.10.22')
ac._run_get_info()
ac._get_state()
