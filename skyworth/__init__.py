#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from . import ac_controller
# from . import ac_model
from . import ac_data
from . import convert


from .ac_controller import AirConditionerController
from .ac_model import AirConditionerModel


class AirConditioner:
    def __init__(self, host: str, port: int = 1998) -> None:
        self.controller = AirConditionerController(host, port)
        self.model = AirConditionerModel(self.controller)
