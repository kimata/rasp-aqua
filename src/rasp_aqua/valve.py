#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPIO を使ってバルブを制御します．

Usage:
  valve.py [-c CONFIG]

Options:
  -c CONFIG     : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

import enum
import logging

import my_lib.rpi


class TARGET(enum.Enum):
    CO2 = 1
    AIR = 2


gpio_air = None
gpio_co2 = None


def init(air=17, co2=27):
    global gpio_air
    global gpio_co2

    gpio_air = air
    gpio_co2 = co2

    my_lib.rpi.gpio.setwarnings(False)
    my_lib.rpi.gpio.setmode(my_lib.rpi.gpio.BCM)

    my_lib.rpi.gpio.setup(gpio_air, my_lib.rpi.gpio.OUT)
    my_lib.rpi.gpio.setup(gpio_co2, my_lib.rpi.gpio.OUT)

    control(TARGET.AIR, my_lib.rpi.gpio.LOW)
    control(TARGET.CO2, my_lib.rpi.gpio.LOW)


def control(target, level):
    global gpio_air
    global gpio_co2

    logging.info("valve {target} = {level}".format(target=target.name, level=level.name))

    if target == TARGET.CO2:
        my_lib.rpi.gpio.output(gpio_co2, level.value)
    elif target == TARGET.AIR:
        my_lib.rpi.gpio.output(gpio_air, level.value)
    else:
        logging.warning("Unknown level: {level}".format(levele=level))


if __name__ == "__main__":
    import local_lib.config
    import local_lib.logger
    from docopt import docopt

    args = docopt(__doc__)

    local_lib.logger.init("test", level=logging.DEBUG)

    config = local_lib.config.load(args["-c"])

    init(config["valve"]["air"]["gpio"], config["valve"]["co2"]["gpio"])

    control(TARGET.AIR, my_lib.rpi.gpio.level[config["valve"]["air"]["mode"]["on"]])
    control(TARGET.CO2, my_lib.rpi.gpio.level[config["valve"]["co2"]["mode"]["on"]])
