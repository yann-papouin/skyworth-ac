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

from skyworth import AirConditioner
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

# Create console handler with a higher log level
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.DEBUG)

# Create file handler 
log_stream_handler.setFormatter(formatter)
log_file_handler = logging.FileHandler(LOG_FILENAME)
log_file_handler.setFormatter(formatter)

# Add the handler to the logger
_logger.addHandler(log_stream_handler)
_logger.addHandler(log_file_handler)

# Enable logger for ac_controller
skyworth.ac_controller._logger.setLevel(logging.DEBUG)
skyworth.ac_controller._logger.addHandler(log_stream_handler)
skyworth.ac_controller._logger.addHandler(log_file_handler)

# Enable logger for ac_model
skyworth.ac_model._logger.setLevel(logging.DEBUG)
skyworth.ac_model._logger.addHandler(log_stream_handler)
skyworth.ac_model._logger.addHandler(log_file_handler)

# ac = AirConditioner('192.168.10.22')
# ac.controller._run_get_info()
# ac.controller._get_state()


def rebuild_menu():
    _menu.TITLE = 'Air Conditioner'
    _menu.ACTIONS = {
        '0': (
            "Exit",
            lambda: _menu.exit(),
        ),
        '1': (
            "Update state",
            lambda: ac.model.update_state(),
            0,
        ),
        '1a':
            (
                "Switch light ON: {}".format(ac.model.light_get()),
                lambda: ac.model.light_on(),
                0,
            ),
        '1b':
            (
                "Switch light OFF: {}".format(ac.model.light_get()),
                lambda: ac.model.light_off(),
                0,
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
    ac.model.update_state()
    rebuild_menu()

    def post(choice, description):
        rebuild_menu()

    _menu.post_action_fn = post
    _menu.show_menu()