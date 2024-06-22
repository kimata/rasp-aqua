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


class MODE(enum.Enum):
    CO2 = 1
    AIR = 2


def is_rasberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        if "BCM" in cpuinfo:
            return True
        else:
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


# STAT_DIR_PATH = pathlib.Path("/dev/shm")

# # STATE が WORKING になった際に作られるnnファイル．Duty 制御している場合，
# # OFF Duty から ON Duty に遷移する度に変更日時が更新される．
# # STATE が IDLE になった際に削除される．
# # (OFF Duty になって実際にバルブを閉じただけでは削除されない)
# STAT_PATH_VALVE_STATE_WORKING = STAT_DIR_PATH / "unit_cooler" / "valve" / "state" / "working"

# # STATE が IDLE になった際に作られるファイル．
# # (OFF Duty になって実際にバルブを閉じただけでは作られない)
# # STATE が WORKING になった際に削除される．
# STAT_PATH_VALVE_STATE_IDLE = STAT_DIR_PATH / "unit_cooler" / "valve" / "state" / "idle"

# # 実際にバルブを開いた際に作られるファイル．
# # 実際にバルブを閉じた際に削除される．
# STAT_PATH_VALVE_OPEN = STAT_DIR_PATH / "unit_cooler" / "valve" / "open"

# # 実際にバルブを閉じた際に作られるファイル．
# # 実際にバルブを開いた際に削除される．
# STAT_PATH_VALVE_CLOSE = STAT_DIR_PATH / "unit_cooler" / "valve" / "close"


# # 電磁弁制御用の GPIO 端子番号．
# # この端子が H になった場合に，水が出るように回路を組んでおく．
# GPIO_PIN_DEFAULT = 17

# pin_no = GPIO_PIN_DEFAULT
# valve_lock = None
# ctrl_hist = []

gpio_air = None
gpio_co2 = None


def init(air=17, co2=27):
    global gpio_air
    global gpio_co2

    gpio_air = air
    gpio_co2 = co2

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(gpio_air, GPIO.OUT)
    GPIO.setup(gpio_co2, GPIO.OUT)

    control()


def control(mode=MODE.AIR):
    global gpio_air
    global gpio_co2

    if mode == MODE.CO2:
        GPIO.output(gpio_air, 0)
        GPIO.output(gpio_co2, 1)
    elif mode == MODE.AIR:
        GPIO.output(gpio_air, 1)
        GPIO.output(gpio_co2, 0)
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

    control(MODE.AIR)
    control(MODE.CO2)
