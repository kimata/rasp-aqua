#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO を使ってバルブを制御します．

Usage:
  valve.py [-c CONFIG]

Options:
  -c CONFIG     : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""
import logging
import enum


class TARGET(enum.Enum):
    CO2 = 1
    AIR = 2


class MODE(enum.Enum):
    ON = 1
    OFF = 0


gpio_air = None
gpio_co2 = None


def is_rasberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        if "BCM" in cpuinfo:
            return True
        else:
            logging.warning(
                "Since it is not running on a Raspberry Pi, the GPIO library is replaced with dummy functions."
            )
            return False
    except Exception as e:
        return False


if is_rasberry_pi():  # pragma: no cover
    import RPi.GPIO as GPIO
else:
    # NOTE: 本物の GPIO のように振る舞うダミーのライブラリ
    class GPIO:
        IS_DUMMY = True
        BCM = 0
        OUT = 0
        state = {}

        def setmode(mode):
            return

        def setup(gpio, direction):
            return

        def output(gpio, value):
            logging.debug("output GPIO_{gpio} = {value}".format(gpio=gpio, value=value))
            GPIO.state[gpio] = value

        def input(gpio):
            if gpio in GPIO.state:
                logging.debug("input GPIO_{gpio} = {value}".format(gpio=gpio, value=GPIO.state[gpio]))
                return GPIO.state[gpio]
            else:
                return 0

        def setwarnings(warnings):
            return


def init(air=17, co2=27):
    global gpio_air
    global gpio_co2

    gpio_air = air
    gpio_co2 = co2

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(gpio_air, GPIO.OUT)
    GPIO.setup(gpio_co2, GPIO.OUT)

    control(TARGET.AIR, MODE.ON)
    control(TARGET.CO2, MODE.OFF)


def control(target, mode):
    global gpio_air
    global gpio_co2

    logging.info("valve {target} = {mode}".format(target=target.name, mode=mode.name))

    if target == TARGET.CO2:
        GPIO.output(gpio_co2, mode.value)
    elif target == TARGET.AIR:
        GPIO.output(gpio_air, mode.value)
    else:
        logging.warning("Unknown mode: {mode}".format(mode=mode))


if __name__ == "__main__":
    from docopt import docopt

    import local_lib.logger
    import local_lib.config

    args = docopt(__doc__)

    local_lib.logger.init("test", level=logging.DEBUG)

    config = local_lib.config.load(args["-c"])

    init()

    control(TARGET.AIR, MODE.ON)
    control(TARGET.CO2, MODE.OFF)
