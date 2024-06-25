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


class GPIO(enum.Enum):
    H = 1
    L = 0


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
    import RPi.GPIO
else:
    # NOTE: 本物の GPIO のように振る舞うダミーのライブラリ
    class RPi:
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
                RPi.GPIO.state[gpio] = value

            def input(gpio):
                if gpio in RPi.GPIO.state:
                    logging.debug("input GPIO_{gpio} = {value}".format(gpio=gpio, value=RPi.GPIO.state[gpio]))
                    return RPi.GPIO.state[gpio]
                else:
                    return 0

            def setwarnings(warnings):
                return


def init(air=17, co2=27):
    global gpio_air
    global gpio_co2

    gpio_air = air
    gpio_co2 = co2

    RPi.GPIO.setwarnings(False)
    RPi.GPIO.setmode(RPi.GPIO.BCM)

    RPi.GPIO.setup(gpio_air, RPi.GPIO.OUT)
    RPi.GPIO.setup(gpio_co2, RPi.GPIO.OUT)

    control(TARGET.AIR, GPIO.L)
    control(TARGET.CO2, GPIO.L)


def control(target, level):
    global gpio_air
    global gpio_co2

    logging.info("valve {target} = {level}".format(target=target.name, level=level.name))

    if target == TARGET.CO2:
        RPi.GPIO.output(gpio_co2, level.value)
    elif target == TARGET.AIR:
        RPi.GPIO.output(gpio_air, level.value)
    else:
        logging.warning("Unknown level: {level}".format(levele=level))


if __name__ == "__main__":
    from docopt import docopt

    import local_lib.logger
    import local_lib.config

    args = docopt(__doc__)

    local_lib.logger.init("test", level=logging.DEBUG)

    config = local_lib.config.load(args["-c"])

    init(config["valve"]["air"]["gpio"], config["valve"]["co2"]["gpio"])

    control(TARGET.AIR, GPIO[config["valve"]["air"]["mode"]["on"]])
    control(TARGET.CO2, GPIO[config["valve"]["co2"]["mode"]["on"]])
