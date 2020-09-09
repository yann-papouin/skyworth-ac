#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from enum import IntEnum
from symbol import power
from .ac_controller import AirConditionerController, Mode

_logger = logging.getLogger(__name__)


class ControlAction(IntEnum):
    OFF = 0
    ON = 1

    @classmethod
    def to_bool(action) -> bool:
        return (action == ControlAction.ON)


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


class AirConditionerModel:
    def __init__(self, controller: AirConditionerController) -> None:
        self.controller = controller
        self._reset_states()

    def _reset_states(self):
        _logger.info('_reset_states')
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

    def _save_swing_state(self):
        # saveWindDirection
        current_mode = self.mode_get()
        self._swing_state[current_mode] = self.data3
        _logger.debug(
            "Swing state for %s saved to %d",
            current_mode,
            self._swing_state[current_mode],
        )

    def _restore_swing_state(self):
        # remember____WindDirection
        current_mode = self.mode_get()
        self.data3 = self._swing_state[current_mode]
        pass

    def _save_fan_speed(self):
        # saveWindSpeed
        current_mode = self.mode_get()
        self._fan_speed[current_mode] = self.controller._get_fan_speed()
        _logger.debug(
            "Fan speed for %s saved to %d",
            current_mode,
            self._fan_speed[current_mode],
        )

    def _restore_fan_speed(self):
        # remember____WindSpeed
        current_mode = self.mode_get()
        speed = self._fan_speed[current_mode]
        _logger.debug(
            "Restore fan speed for %s to %d",
            current_mode,
            self._swing_state[current_mode],
        )
        self.controller._set_fan_speed(speed)

    def _save_temperature_set(self):
        _logger.info('_save_temperature_set')
        current_mode = self.mode_get()
        self._temperature_set[current_mode
                             ] = self.controller._get_temperature_set()
        _logger.debug(
            "Temperature set for %s saved to %d",
            current_mode,
            self._temperature_set[current_mode],
        )

    def _restore_temperature_set(self):
        # Check for getFahrenheitByte in original implementation
        current_mode = self.mode_get()
        temperature = self._temperature_set[current_mode]
        _logger.debug(
            "Restore temperature set for %s to %d",
            current_mode,
            self._temperature_set[current_mode],
        )
        self.controller._set_temperature_set(temperature)

    def update_state(self):
        _logger.info('update_state')
        self.controller._run_get_info()
        self.controller._get_state()

    @property
    def power(self) -> ControlAction:
        _logger.info('power_get')
        value = self.controller._get_power()
        return ControlAction.ON if value else ControlAction.OFF

    @power.setter
    def power(self, value: ControlAction):
        _logger.info('power_set')
        self.controller._set_power(ControlAction.to_bool(value))
        self.controller._run_command()

    @property
    def mute(self) -> ControlAction:
        _logger.info('mute_get')
        value = self.controller._get_mute()
        return ControlAction.ON if value else ControlAction.OFF

    @mute.setter
    def mute(self, value: ControlAction):
        _logger.info('mute_set')
        self.controller._set_mute(ControlAction.to_bool(value))
        self.controller._run_command()

    @property
    def swing(self) -> SwingAction:
        _logger.info('swing_get')
        lr = self.controller._get_swing_left_right()
        ud = self.controller._get_swing_up_down()
        if lr and ud:
            res = SwingAction.ALL
        elif lr and not ud:
            res = SwingAction.LEFT_RIGHT
        elif not lr and ud:
            res = SwingAction.UP_DOWN
        else:
            res = SwingAction.OFF
        return res

    @swing.setter
    def swing(self, action: SwingAction):
        _logger.info('swing_set')
        self.controller._set_power(True)
        if action == SwingAction.OFF:
            self.controller._set_swing_off()
        elif action == SwingAction.LEFT_RIGHT:
            self.controller._set_swing_left_right(True)
            self.controller._set_swing_up_down(False)
        elif action == SwingAction.UP_DOWN:
            self.controller._set_swing_up_down(True)
            self.controller._set_swing_left_right(False)
        elif action == SwingAction.ALL:
            self.controller._set_swing_up_down(True)
            self.controller._set_swing_left_right(True)
        self.controller._save_swing_state()

    @property
    def mode(self) -> ModeAction:
        _logger.info('mode_get')
        mode = self.controller._get_mode()
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

    @mode.setter
    def mode(self, action: ModeAction):
        _logger.info('mode_set')
        self.controller._set_power(True)
        if action == ModeAction.AUTO:
            self.controller._set_power(True)
            self.controller._set_turbo(False)
            self.controller._set_mode(Mode.AUTO)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self.controller._set_mute(False)
            self._restore_swing_state()
            self.controller._set_auxiliary_heating(False)
            self.controller._set_sleep(False)
            self.controller._set_energy_saving(False)
        elif action == ModeAction.COOL:
            self.controller._set_power(True)
            self.controller._set_mode(Mode.COOL)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self.controller._set_mute(False)
            self._restore_swing_state()
            self.controller._set_auxiliary_heating(False)
            self.controller._set_sleep(False)
            self.controller._set_energy_saving(False)
        elif action == ModeAction.HEAT:
            self.controller._set_power(True)
            self.controller._set_mode(Mode.HEAT)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self.controller._set_mute(False)
            self._restore_swing_state()
            self.controller._set_auxiliary_heating(True)
            self.controller._set_sleep(False)
            self.controller._set_energy_saving(False)
        elif action == ModeAction.DEHUMIDIFIER:
            self.controller._set_power(True)
            self.controller._set_mode(Mode.DEHUMIDIFIER)
            self.controller._set_turbo(False)
            self.controller._set_fan_speed(1)
            self._restore_temperature_set()
            self.controller._set_mute(False)
            self._restore_swing_state()
            self.controller._set_auxiliary_heating(False)
            self.controller._set_sleep(False)
            self.controller._set_energy_saving(False)
        elif action == ModeAction.FAN:
            self.controller._set_power(True)
            self.controller._set_mode(Mode.FAN)
            self._restore_fan_speed()
            self._restore_temperature_set()
            self.controller._set_mute(False)
            self._restore_swing_state()
            self.controller._set_auxiliary_heating(False)
            self.controller._set_sleep(False)
            self.controller._set_energy_saving(False)
        else:
            raise Exception("Unknown ModeAction")
        self.controller._run_command()

    @property
    def temperature_set(self) -> int:
        _logger.info('temperature_set_get')
        temperature_set = self.controller._get_temperature_set()
        return temperature_set

    @temperature_set.setter
    def temperature_set(self, value: int):
        _logger.info('temperature_set_set')
        self.controller._set_temperature_set(value)
        self.controller._run_command()
        self._save_temperature_set()

    @property
    def speed(self) -> SpeedAction:
        _logger.info('speed_get')
        speed = self.controller._get_fan_speed()
        return SpeedAction(speed)

    @speed.setter
    def speed(self, speed: SpeedAction):
        _logger.info('speed_set')
        self.controller._set_power(True)
        self.controller._set_turbo(False)
        self.controller._set_mute(False)
        self.controller._set_fan_speed(speed)
        self.controller._run_command()
        self._save_fan_speed()

    @property
    def sleep(self) -> ControlAction:
        _logger.info('sleep_get')
        value = self.controller._get_sleep()
        return ControlAction.ON if value else ControlAction.OFF

    @sleep.setter
    def sleep(self, value: ControlAction):
        _logger.info('sleep_set')
        current_mode = self.controller.mode_get()
        self.controller._set_power(True)

        if current_mode not in (ModeAction.AUTO, ModeAction.FAN):
            self.controller._set_sleep(ControlAction.to_bool(value))
            # TODO: Check if condition is ok
            if not value:
                self.controller._set_energy_saving(False)
        else:
            self.controller._set_sleep(ControlAction.to_bool(ControlAction.OFF))
        self.controller._run_command()

    @property
    def filter_pm(self) -> ControlAction:
        _logger.info('filter_pm_get')
        value = self.controller._get_filter()
        return ControlAction(value)

    @filter_pm.setter
    def filter_pm(self, value: ControlAction):
        _logger.info('filter_pm_set')
        self.controller._set_power(True)
        self.controller._set_filter(ControlAction.to_bool(value))
        self.controller._run_command()

    @property
    def energy_saving(self) -> ControlAction:
        _logger.info('energy_saving_get')
        value = self.controller._get_energy_saving()
        return ControlAction(value)

    @energy_saving.setter
    def energy_saving(self, value: ControlAction):
        _logger.info('energy_saving_set')
        self.controller._set_power(True)
        self.controller._set_energy_saving(ControlAction.to_bool(value))
        self.controller._run_command()

    @property
    def turbo(self) -> ControlAction:
        _logger.info('turbo_get')
        value = self.controller._get_turbo()
        return ControlAction(value)

    @turbo.setter
    def turbo(self, value: ControlAction):
        _logger.info('turbo_set')
        self.controller._set_power(True)
        self.controller._set_turbo(ControlAction.to_bool(value))
        self.controller._run_command()

    @property
    def light(self) -> ControlAction:
        _logger.info('light_get')
        value = self.controller._get_light()
        return ControlAction.ON if value else ControlAction.OFF

    @light.setter
    def light(self, value: ControlAction):
        _logger.info('light_set')
        self.controller._run_get_info()
        self.controller._set_light(ControlAction.to_bool(value))
        self.controller._run_command()
        self.controller._run_get_info()

    def temperature_mode_F2C(self):
        _logger.info('temperature_mode_F2C')
        self.controller._set_temperature_mode(False)
        self.controller._run_command()

    def temperature_mode_C2F(self):
        _logger.info('temperature_mode_C2F')
        self.controller._set_temperature_mode(True)
        self.controller._run_command()
