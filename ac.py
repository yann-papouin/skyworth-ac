#!/bin/python

import socket
import logging
from enum import Enum

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


def barray2sblist(value):
    return [byte2sbyte(x) for x in list(value)]


# CRC [ 107, -69]

from crcmod.predefined import mkPredefinedCrcFun
modbus_crc = mkPredefinedCrcFun('modbus')


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


class ControlAction(Enum):
    OFF = 0
    ON = 1


class SwingAction(Enum):
    OFF = 0
    LEFT_RIGHT = 1
    UP_DOWN = 2
    ALL = 2


class ModeAction(Enum):
    AUTO = 0
    COOL = 1
    HEAT = 2
    DEHUMIDIFIER = 3
    FAN = 4

class ModeSpeed(Enum):
    AUTO = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
    SPEED_4 = 4


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

    def count(self) -> int:
        1 + 1
        return False

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

    def get_info(self):
        TYPE_GET_INFO = 0xa1  # -89
        # infoLength = MqttWireMessage.MESSAGE_TYPE_PINGRESP; // 13
        # srcAddress = -43;
        # dstAddress = WIFIADDR; // WIFIADDR = -47;
        # acCOMD = -89;
        # byte[] ch = {122, 122, dstAddress, srcAddress, infoLength, acID1, acID2, acCOMD, acDATA0, acDATA1, (byte) cmd};
        # byte[] checkCodeHL = CRC16.GetCRC16(ch);
        # byte[] res = new byte[infoLength];
        # System.arraycopy(ch, 0, res, 0, ch.length);
        # System.arraycopy(checkCodeHL, 0, res, ch.length, checkCodeHL.length);
        # showBinary(res);
        # return res;
        self._send(TYPE_GET_INFO)

        #         case 100:
        #     String str4 = "ON";
        #     data1 = (byte) ((data1 & 247) | getPower(1));
        #     break;
        # case 101:
        #     String str5 = "OFF";
        #     data1 = (byte) ((data1 & 247) | getPower(0));
        #     break;

    def _get_mode_from_state(self):
        # Mode const for binary comparison with control bit
        AUTO = 107
        COOL = 108
        HEAT = 109
        DEHUMIDIFIER = 110
        FAN = 111

        control = self.data1 & 7
        if control == AUTO:
            res = ModeAction.AUTO
        elif control == COOL:
            res = ModeAction.COOL
        elif control == HEAT:
            res = ModeAction.HEAT
        elif control == DEHUMIDIFIER:
            res = ModeAction.DEHUMIDIFIER
        elif control == FAN:
            res = ModeAction.FAN
        else:
            res = ModeAction.AUTO

        return res

    def _set_power(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 3) % 255
        self.data1 = (self.data1 & Command.POWER) | controlbit

    def _set_turbo(self, state: bool):
        # Also called super mode
        control = 1 if state else 0
        controlbit = (control << 7) % 255
        self.data1 = (self.data1 & Command.TURBO) | controlbit

    def _set_mode(self, value: int):
        controlbit = (value << 0) % 255
        self.data1 = (self.data1 & Command.MODE) | controlbit

    def _set_swing_off(self):
        self.data3 = 0

    def _set_swing_left_right(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 4) % 255
        self.data3 = (self.data3 & Command.WIND_LEFT_RIGHT) | controlbit

    def _set_swing_up_down(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 0) % 255
        self.data3 = (self.data3 & Command.WIND_UP_DOWN) | controlbit

    def _set_fan_speed(self, value: int):
        controlbit = (value << 4) % 255
        self.data1 = (self.data1 & Command.FAN_SPEED) | controlbit

    def _save_swing_state(self):
        # saveWindDirection
        current_mode = self._get_mode_from_state()
        self._swing_state[current_mode] = self.data3
        pass

    def _restore_swing_state(self):
        # remember____WindDirection
        current_mode = self._get_mode_from_state()
        self.data3 = self._swing_state[current_mode]
        pass

    def _save_fan_speed(self):
        # saveWindSpeed
        current_mode = self._get_mode_from_state()
        self._fan_speed[current_mode] = 0
        pass

    def _restore_fan_speed(self):
        # remember____WindSpeed
        current_mode = self._get_mode_from_state()
        speed = self._fan_speed[current_mode]
        self._set_fan_speed(speed)

    def _save_temperature_set(self):
        current_mode = self._get_mode_from_state()
        self._temperature_set[current_mode] = 0

    def _restore_temperature_set(self):
        # Check for getFahrenheitByte in original implementation
        current_mode = self._get_mode_from_state()
        temperature = self._temperature_set[current_mode]
        self.data2 = (self.data2 & Command.TEMPERATURE_SET) | temperature

    def _set_mute(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 6) % 255
        self.data2 = (self.data2 & Command.MUTE) | controlbit

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

    def _set_auxiliary_heating(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 4) % 255
        self.data4 = (self.data4 & Command.AUXILIARY_HEATING) | controlbit

    def _set_sleep(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 1) % 255
        self.data4 = (self.data4 & Command.SLEEP) | controlbit

    def _set_energy_saving(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 0) % 255
        self.data4 = (self.data4 & Command.ENERGY_SAVING) | controlbit

    def _set_light(self, state: bool):
        control = 1 if state else 0
        controlbit = (control << 7) % 255
        self.data4 = (self.data4 & Command.LIGHT) | controlbit

    def power_on(self):
        self._set_power(True)
        self._run_command()

    def power_off(self):
        self._set_power(False)
        self._run_command()

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
        AUTO = 0
        COOL = 1
        HEAT = 4
        DEHUMIDIFIER = 2
        FAN = 3
        self._set_power(True)
        if action == ModeAction.AUTO:
            self._set_power(True)
            self._set_turbo(False)
            self._set_mode(AUTO)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.COOL:
            self._set_power(True)
            self._set_mode(COOL)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.HEAT:
            self._set_power(True)
            self._set_mode(HEAT)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(True)
            self._set_sleep(False)
            self._set_energy_saving(False)
        elif action == ModeAction.DEHUMIDIFIER:
            self._set_power(True)
            self._set_mode(DEHUMIDIFIER)
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
            self._set_mode(FAN)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self._set_mute(False)
            self._restore_swing_state()
            self._set_auxiliary_heating(False)
            self._set_sleep(False)
            self._set_energy_saving(False)
        else:
            raise Exception("Unknown ModeAction")

    def speed_set(self, speed: ModeSpeed):
        self._set_power(True)
        self._set_turbo(False)
        self._set_mute(False)
        self._set_fan_speed(speed)

    def light_on(self):
        self._set_light(True)
        self._run_command()

    def light_off(self):
        self._set_light(False)
        self._run_command()

    def _run_command(self, command: Command):
        TYPE_COMMAND = 0xa1  # -95
        # self.data1 = 4
        # self.data2 = 72
        # self.data3 = 0
        # self.data4 = command
        data = [
            self.data13, self.data14, self.data1, self.data2, self.data3,
            self.data4, self.data5, self.data6, self.data7, self.data8,
            self.data9, self.data10
        ]
        self._send(TYPE_COMMAND, data)

    def _send(self, type, data=[]):

        # Build datagram with message data
        HEADER = 0x7a  # 122
        DST_ADDRESS = 0x21  # 33 # ?
        SRC_ADDRESS = 0xd5  # 43 # ?
        AC_ID1 = 0  # ? Not used
        AC_ID2 = 0  # ? Not used

        AC_DATA0 = 0x0a  # 10 ?
        AC_DATA1 = 0x0a  # 10 ?

        #LENGTH = 0x18  # 24
        BASE_LENGTH = 0x0a  # 10
        CRC_LENGTH = 0x02  # 2

        LENGTH = BASE_LENGTH + len(data) + CRC_LENGTH

        raw_message = [
            HEADER, HEADER, DST_ADDRESS, SRC_ADDRESS, LENGTH, AC_ID1, AC_ID2,
            type, AC_DATA0, AC_DATA1
        ] + data

        crc16 = modbus_crc(bytearray(raw_message))
        crc_array = [
            (crc16 >> 8) & 0xff,
            crc16 & 0xff,
        ]

        raw_message += crc_array
        self._raw_send(raw_message)

    def _raw_send(self, message: list):
        BUFFER_SIZE = 1024

        raw_message = bytearray(message)
        _logger.debug("data >> %s", barray2sblist(raw_message))

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(raw_message)
        raw_data = s.recv(BUFFER_SIZE)
        s.close()

        _logger.debug("data << %s", barray2sblist(raw_data))
        return raw_data


# MESSAGE:       [122, 122, 33, -43, 24, 0, 0, -95, 10, 10, 0, 0, 4, 72, 0, 0, 0, 0, 0, 0, 0, 0, 107, -69]
# received data: [122, 122, -43, 33, 28, 0, 0, -93, 10, 10, 24, 5, 0, 4, 72, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -13, -26]

# import time
# ac = AirConditionner('192.168.10.22')
# ac.light_on()
# time.sleep(1)
# ac.light_off()
# time.sleep(1)