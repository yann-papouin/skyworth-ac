#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import argparse
import logging
import time

import skyworth.ac_controller
import skyworth.ac_model
import skyworth.ac_data

from skyworth import AirConditioner
from skyworth.ac_model import (
    SpeedAction,
    ModeAction,
    SwingAction,
    ControlAction,
    TemperatureMode,
)
from ui import _menu

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

LOG_DIR = os.path.join(
    os.getcwd(),
    'logs',
)
LOG_FILE = 'ac-{0}.log'.format(time.strftime("%H-%M_%S"), )

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOG_FILENAME = os.path.join(LOG_DIR, LOG_FILE)

# Create formatter and add it to the handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

LOG_LEVEL = logging.DEBUG

# Create console handler with a higher log level
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(LOG_LEVEL)

# Create file handler
log_stream_handler.setFormatter(formatter)
log_file_handler = logging.FileHandler(LOG_FILENAME)
log_file_handler.setFormatter(formatter)


def enabled_logging(logger):
    logger.setLevel(LOG_LEVEL)
    # Add handlers to the logger
    logger.addHandler(log_stream_handler)
    logger.addHandler(log_file_handler)


# Enable logger for main
enabled_logging(_logger)
# Enable logger for ac_controller
enabled_logging(skyworth.ac_controller._logger)
# Enable logger for ac_model
enabled_logging(skyworth.ac_model._logger)
# Enable logger for ac_data
enabled_logging(skyworth.ac_data._logger)

ac = None


def interactive_temperature_set(ac: AirConditioner):
    print("Enter a new temperature (16-47).\n")
    res = input()
    try:
        temperature = int(res)
        if temperature not in range(
            skyworth.ac_controller.RAW_MIN, skyworth.ac_controller.RAW_MAX
        ):
            raise ValueError("Value out of range")
        ac.model.temperature_set = temperature
        rebuild_menu()
    except Exception as e:
        print(e)


def set_property(prop, value):
    prop = value


def rebuild_menu(advanced_menu=False):
    ac.model.update_state()

    if not advanced_menu:
        _menu.TITLE = 'Air Conditioner'
        _menu.ACTIONS = {
            '0': (
                "Exit",
                lambda: _menu.exit(),
            ),
            '1':
                (
                    "Update state",
                    lambda: ac.model.update_state(),
                    0,
                    '',
                    '-------------------------------',
                ),
            '10':
                (
                    "Set temperature = %d" % ac.model.temperature_set,
                    lambda: interactive_temperature_set(ac),
                ),
            '11a':
                (
                    "Switch temperature mode to CELSIUS",
                    lambda: ac.model.temperature_mode_celsius(),
                    0,
                    "Mode = %s" % ac.model.temperature_mode,
                ),
            '11b':
                (
                    "Switch temperature mode to FAHRENHEIT",
                    lambda: ac.model.temperature_mode_fahrenheit(),
                    0,
                ),
            '1a':
                (
                    "Switch power ON",
                    lambda: ac.model.power_on(),
                    0,
                    "Power = %s" % ac.model.power,
                ),
            '1b': (
                "Switch power OFF",
                lambda: ac.model.power_off(),
                0,
            ),
            '2a':
                (
                    "Switch light ON",
                    lambda: ac.model.light_on(),
                    0,
                    "Light = %s" % ac.model.light,
                ),
            '2b': (
                "Switch light OFF",
                lambda: ac.model.light_off(),
                0,
            ),
            '3a':
                (
                    "Switch mute ON",
                    lambda: ac.model.mute_on(),
                    0,
                    "Mute = %s" % ac.model.mute,
                ),
            '3b': (
                "Switch mute OFF",
                lambda: ac.model.mute_off(),
                0,
            ),
            '4a':
                (
                    "Switch PM 2.5 filter ON",
                    lambda: ac.model.filter_pm_on(),
                    0,
                    "PM 2.5 filter = %s" % ac.model.filter_pm,
                ),
            '4b':
                (
                    "Switch PM 2.5 filter OFF",
                    lambda: ac.model.filter_pm_off(),
                    0,
                ),
            '5a':
                (
                    "Switch energy saving ON",
                    lambda:
                    ac.model.energy_saving_on(),
                    0,
                    "Energy saving = %s" % ac.model.energy_saving,
                ),
            '5b':
                (
                    "Switch energy saving OFF",
                    lambda:
                    ac.model.energy_saving_off(),
                    0,
                ),
            '6a':
                (
                    "Switch turbo ON",
                    lambda: ac.model.turbo_on(),
                    0,
                    "Turbo = %s" % ac.model.turbo,
                ),
            '6b':
                (
                    "Switch turbo OFF",
                    lambda: ac.model.turbo_off(),
                    0,
                ),
            '7':
                (
                    "Mode: %s" % ac.model.mode,
                    lambda: rebuild_menu('mode'),
                    0,
                    '-------------------------------',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
            '8':
                (
                    "Speed: %s" % ac.model.speed,
                    lambda: rebuild_menu('speed'),
                    0,
                    '',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
            '9':
                (
                    "Swing: %s" % ac.model.swing,
                    lambda: rebuild_menu('swing'),
                    0,
                    '',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
        }

    elif advanced_menu == 'speed':
        _menu.TITLE = _menu.ACTIONS[_menu.last_choice][0]
        _menu.ACTIONS = {
            '0':
                (
                    "Back",
                    lambda: rebuild_menu(),
                    0,
                    '',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
            '1':
                (
                    "Speed 1",
                    lambda: ac.model.speed_1(),
                ),
            '2':
                (
                    "Speed 2",
                    lambda: ac.model.speed_2(),
                ),
            '3':
                (
                    "Speed 3",
                    lambda: ac.model.speed_3(),
                ),
            '4':
                (
                    "Speed 4",
                    lambda: ac.model.speed_4(),
                ),
            '5':
                (
                    "Speed 5",
                    lambda: ac.model.speed_5(),
                ),
            '6':
                (
                    "Speed 6",
                    lambda: ac.model.speed_6(),
                ),
            '7':
                (
                    "Speed Auto",
                    lambda: ac.model.speed_auto(),
                ),
        }
    elif advanced_menu == 'mode':
        _menu.TITLE = _menu.ACTIONS[_menu.last_choice][0]
        _menu.ACTIONS = {
            '0':
                (
                    "Back",
                    lambda: rebuild_menu(),
                    0,
                    '',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
            '1':
                (
                    "Auto",
                    lambda: ac.model.mode_auto(),
                ),
            '2':
                (
                    "Cool",
                    lambda: ac.model.mode_cool(),
                ),
            '3':
                (
                    "Heat",
                    lambda: ac.model.mode_heat(),
                ),
            '4':
                (
                    "Dehumidifier",
                    lambda:
                    ac.model.mode_dehumidifier(),
                ),
            '5': (
                "Fan",
                lambda: ac.model.mode_fan(),
            ),
        }

    elif advanced_menu == 'swing':
        _menu.TITLE = _menu.ACTIONS[_menu.last_choice][0]
        _menu.ACTIONS = {
            '0':
                (
                    "Back",
                    lambda: rebuild_menu(),
                    0,
                    '',
                    '',
                    _menu.ActionWaitMode.NO_WAIT,
                ),
            '1':
                (
                    "Off",
                    lambda: ac.model.swing_off(),
                ),
            '2':
                (
                    "Left/Right",
                    lambda:
                     ac.model.swing_left_right(),
                ),
            '3':
                (
                    "Up/Down",
                    lambda:  ac.model.swing_up_down(),
                ),
            '4':
                (
                    "All/Left/Right/Up/Down",
                    lambda:  ac.model.swing_all(),
                ),
        }


if __name__ == "__main__":
    args = sys.argv[1:]
    print_help = (len(args) == 0)
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'host',
        metavar='host',
        type=str,
        help='Hostname or IP',
    )

    parser.add_argument(
        'port',
        metavar='port',
        type=int,
        help='Port (1024-65535)',
        default=1998
    )

    args = parser.parse_args(args)

    if print_help:
        parser.print_help()
        exit()

    ac = AirConditioner(args.host, args.port)
    rebuild_menu()

    def pre(choice, description):
        _menu.last_choice = choice

    def post(choice, description):
        pass

    _menu.pre_action_fn = pre
    _menu.post_action_fn = post
    _menu.show_menu()