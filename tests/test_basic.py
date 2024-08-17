#!/usr/bin/env python3
# ruff: noqa: S101

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
    import my_lib.config
    import my_lib.rpi

    config = my_lib.config.load(CONFIG_FILE)

    import my_lib.footprint

    my_lib.footprint.clear(pathlib.Path(config["liveness"]["file"]["scheduler"]))
    my_lib.rpi.gpio.hist_clear()


def gpio_check(expect_list):
    import logging

    import my_lib.rpi

    hist_list = my_lib.rpi.gpio.hist_get()

    logging.debug(hist_list)

    assert hist_list == expect_list


######################################################################
def test_init_CO2_off_AIR_on(freezer):
    freezer.move_to("07:00")
    rasp_aqua.control.execute(my_lib.config.load(CONFIG_FILE), 1)
    time.sleep(1)
    rasp_aqua.control.term()

    gpio_check([{"state": "low"}, {"state": "low"}, {"state": "low"}, {"state": "low"}])


def test_init_CO2_off_AIR_off(freezer):
    config = my_lib.config.load(CONFIG_FILE)

    freezer.move_to("09:00")

    rasp_aqua.control.execute(config, 1)
    time.sleep(1)
    rasp_aqua.control.term()

    gpio_check(
        [
            {"state": "low"},
            {"state": "low"},
            {"pin_num": config["valve"]["air"]["gpio"], "state": "high"},
            {"state": "low"},
        ]
    )


def test_init_CO2_on_AIR_off(freezer):
    config = my_lib.config.load(CONFIG_FILE)

    freezer.move_to("012:00")

    rasp_aqua.control.execute(config, 1)
    time.sleep(1)
    rasp_aqua.control.term()

    gpio_check(
        [
            {"state": "low"},
            {"state": "low"},
            {"pin_num": config["valve"]["air"]["gpio"], "state": "high"},
            {"pin_num": config["valve"]["co2"]["gpio"], "state": "high"},
        ]
    )


# def test_init(freezer):
#     freezer.move_to("08:00")
#     rasp_aqua.control.execute(my_lib.config.load(CONFIG_FILE), 1)

#     rasp_aqua.control.term()

#     hist_list = my_lib.rpi.gpio.hist_get()

#     assert hist_list is None


# air:
#   gpio: 27
#   control:
#     "on": "20:00"
#     "off": "08:00"
#   mode:
#     "on": LOW
#     "off": HIGH

# co2:
#   gpio: 17
#   control:
#     "on": "11:00"
#     "off": "15:00"
#   mode:
#     "on": HIGH
#     "off": LOW
