#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import skyworth.ac_controller
import skyworth.ac_model

from skyworth import AirConditioner
from ui import _menu

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

# Enable logger for ac_*
skyworth.ac_controller._logger.setLevel(logging.DEBUG)
skyworth.ac_controller._logger.addHandler(handler)
skyworth.ac_model._logger.setLevel(logging.DEBUG)
skyworth.ac_model._logger.addHandler(handler)

ac = AirConditioner('192.168.10.22')
ac.controller._run_get_info()
ac.controller._get_state()
