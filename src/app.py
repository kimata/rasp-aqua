#!/usr/bin/env python3
"""
水槽の自動管理を行います．

Usage:
  rasp-aqua.py [-c CONFIG] [-d]

Options:
  -c CONFIG     : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -d                : デバッグモードで動作します．
"""

import datetime
import logging
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool

import pytz

import rasp_aqua.scheduler
import rasp_aqua.valve

NAME = "rasp-aqua"
VERSION = "0.1.0"


def check_time_in_range(start, end):
    time_curr = datetime.datetime.now().time()

    time_start = datetime.datetime.strptime(start, "%H:%M").time()
    time_end = datetime.datetime.strptime(end, "%H:%M").time()

    if time_start <= time_end:
        if time_start <= time_curr <= time_end:
            return (True, 0)
        else:
            return (False, 0)
    else:
        if time_curr >= time_start:
            return (True, 1)
        elif time_curr <= time_end:
            return (True, 2)
        else:
            return (False, 1)


# NOTE: 現在時刻に基づいてバルブの状態を設定する
def init_valve(config):
    for target in ["air", "co2"]:
        judge = check_time_in_range(
            config["valve"][target]["control"]["on"], config["valve"][target]["control"]["off"]
        )
        if judge[0]:
            mode = rasp_aqua.valve.GPIO[config["valve"][target]["mode"]["on"]]

            if judge[1] == 0:
                reason = "now is between {start}-{end}".format(
                    start=config["valve"][target]["control"]["on"],
                    end=config["valve"][target]["control"]["off"],
                )
            elif judge[1] == 1:
                reason = "now is after {start}".format(
                    start=config["valve"][target]["control"]["on"],
                )
            elif judge[1] == 2:
                reason = "now is before {end}".format(
                    end=config["valve"][target]["control"]["off"],
                )

        else:
            mode = rasp_aqua.valve.GPIO[config["valve"][target]["mode"]["off"]]

            if judge[1] == 0:
                reason = "now is not between {start}-{end}".format(
                    start=config["valve"][target]["control"]["on"],
                    end=config["valve"][target]["control"]["off"],
                )
            else:
                reason = "now is after {end} and before {start}".format(
                    start=config["valve"][target]["control"]["on"],
                    end=config["valve"][target]["control"]["off"],
                )

        logging.info(
            "initialize {target} {mode}, because {reason}".format(
                target=target,
                mode=mode.name,
                reason=reason,
            )
        )
        rasp_aqua.valve.control(rasp_aqua.valve.TARGET[target.upper()], mode)


def set_schedule(config, queue):
    task_list = []
    for target in ["air", "co2"]:
        for mode in ["on", "off"]:
            task_list.append(
                {
                    "name": "{target} {mode}".format(target=target, mode=mode),
                    "time": config["valve"][target]["control"][mode],
                    "func": rasp_aqua.valve.control,
                    "args": (
                        rasp_aqua.valve.TARGET[target.upper()],
                        rasp_aqua.valve.GPIO[config["valve"][target]["mode"][mode]],
                    ),
                }
            )

    queue.put(task_list)


def execute(config):
    rasp_aqua.valve.init(config["valve"]["air"]["gpio"], config["valve"]["co2"]["gpio"])

    timezone = pytz.timezone("Asia/Tokyo")
    queue = Queue()
    pool = ThreadPool(processes=1)

    result = rasp_aqua.scheduler.init(timezone, queue, config["liveness"]["file"]["scheduler"])

    init_valve(config)
    set_schedule(config, queue)

    result.get()


######################################################################
if __name__ == "__main__":
    import docopt
    import my_lib.config
    import my_lib.logger

    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    debug_mode = args["-d"]

    my_lib.logger.init("hems.rasp-water", level=logging.DEBUG if debug_mode else logging.INFO)

    config = my_lib.config.load(config_file)

    execute(config)
