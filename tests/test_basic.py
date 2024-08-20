#!/usr/bin/env python3
# ruff: noqa: S101

import datetime
import logging
import pathlib
import time
from unittest import mock

import my_lib.config
import my_lib.webapp.config
import pytest
import rasp_aqua.control

CONFIG_FILE = "config.example.yaml"


@pytest.fixture(scope="session", autouse=True)
def env_mock():
    with mock.patch.dict(
        "os.environ",
        {
            "TEST": "true",
            "NO_COLORED_LOGS": "true",
        },
    ) as fixture:
        yield fixture


@pytest.fixture(autouse=True)
def _clear():
    import my_lib.footprint
    import my_lib.rpi

    config = my_lib.config.load(CONFIG_FILE)

    my_lib.footprint.clear(pathlib.Path(config["liveness"]["file"]["scheduler"]))
    my_lib.rpi.gpio.hist_clear()

    yield

    rasp_aqua.control.term()


def move_to(time_machine, hour):
    target_time = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9))).replace(
        hour=hour, minute=0, second=0
    )

    time_machine.move_to(target_time)


def gpio_check(expect_list):
    import my_lib.rpi

    hist_list = my_lib.rpi.gpio.hist_get()

    logging.debug(hist_list)

    hist_list = [{k: v for k, v in d.items() if k not in "high_period"} for i, d in enumerate(hist_list)]

    assert hist_list == expect_list


######################################################################
def test_init_CO2_off_AIR_on(time_machine):
    config = my_lib.config.load(CONFIG_FILE)

    move_to(time_machine, 7)

    rasp_aqua.control.execute(config, 0.1)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
        ]
    )


def test_init_CO2_off_AIR_off(time_machine):
    config = my_lib.config.load(CONFIG_FILE)

    move_to(time_machine, 9)

    rasp_aqua.control.execute(config, 0.1)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
        ]
    )


def test_init_CO2_on_AIR_off(time_machine):
    config = my_lib.config.load(CONFIG_FILE)

    move_to(time_machine, 12)

    rasp_aqua.control.execute(config, 0.1)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["on"]},
        ]
    )


def test_schedule(time_machine):
    config = my_lib.config.load(CONFIG_FILE)

    move_to(time_machine, 7)

    rasp_aqua.control.execute(config, 0.1)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
        ]
    )

    move_to(time_machine, 9)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
        ]
    )

    move_to(time_machine, 12)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["on"]},
        ]
    )

    move_to(time_machine, 16)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
        ]
    )

    move_to(time_machine, 20)
    time.sleep(0.5)

    gpio_check(
        [
            {"pin_num": config["valve"]["air"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": my_lib.rpi.gpio.level.LOW.name},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["off"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["on"]},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": config["valve"]["co2"]["mode"]["off"]},
            {"pin_num": config["valve"]["air"]["gpio"], "state": config["valve"]["air"]["mode"]["on"]},
        ]
    )


def test_healthz():
    import healthz

    config = my_lib.config.load(CONFIG_FILE)

    rasp_aqua.control.execute(config, 0.1)
    time.sleep(0.5)

    assert healthz.check_liveness(config)
