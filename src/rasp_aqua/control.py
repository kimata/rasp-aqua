#!/usr/bin/env python3

import datetime
import logging
import pathlib
from multiprocessing import Queue

import my_lib.rpi
import rasp_aqua.scheduler
import rasp_aqua.valve


def check_time_in_range(start, end):
    timezone = datetime.timezone(datetime.timedelta(hours=rasp_aqua.scheduler.timezone["offset"]))
    time_curr = datetime.datetime.now(tz=timezone).time()

    time_start = datetime.datetime.strptime(start, "%H:%M").replace(tzinfo=timezone).time()
    time_end = datetime.datetime.strptime(end, "%H:%M").replace(tzinfo=timezone).time()

    if time_start <= time_end:
        if time_start <= time_curr <= time_end:
            return (True, 0)
        else:
            return (False, 0)
    else:  # noqa: PLR5501
        if time_curr >= time_start:
            return (True, 1)
        elif time_curr <= time_end:
            return (True, 2)
        else:
            return (False, 1)


# NOTE: 現在時刻に基づいてバルブの状態を設定する
def init_valve(config):
    logging.info(
        "Now is %s",
        datetime.datetime.now(
            tz=datetime.timezone(datetime.timedelta(hours=rasp_aqua.scheduler.timezone["offset"]))
        ).strftime("%Y-%m-%d %H:%M"),
    )

    for target in ["air", "co2"]:
        judge = check_time_in_range(
            config["valve"][target]["control"]["on"], config["valve"][target]["control"]["off"]
        )
        if judge[0]:
            mode = "on"

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
            mode = "off"

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

        logging.info("initialize %s %s, because %s", target, mode.upper(), reason)
        rasp_aqua.valve.control(
            rasp_aqua.valve.TARGET[target.upper()],
            my_lib.rpi.gpio.level[config["valve"][target]["mode"][mode]],
        )


def set_schedule(config, queue):
    task_list = []
    for target in ["air", "co2"]:
        for mode in ["on", "off"]:
            task_list.append(  # noqa: PERF401
                {
                    "name": f"{target} {mode}",
                    "time": config["valve"][target]["control"][mode],
                    "func": rasp_aqua.valve.control,
                    "args": (
                        rasp_aqua.valve.TARGET[target.upper()],
                        my_lib.rpi.gpio.level[config["valve"][target]["mode"][mode]],
                    ),
                }
            )

    queue.put(task_list)


def execute(config, check_interval_sec=10):
    rasp_aqua.valve.init(config["valve"]["air"]["gpio"], config["valve"]["co2"]["gpio"])

    queue = Queue()

    rasp_aqua.scheduler.init(
        config["timezone"], queue, pathlib.Path(config["liveness"]["file"]["scheduler"]), check_interval_sec
    )

    init_valve(config)
    set_schedule(config, queue)


def term():
    if rasp_aqua.scheduler.worker is None:
        return

    rasp_aqua.scheduler.should_terminate.set()
    rasp_aqua.scheduler.worker.join()
    rasp_aqua.scheduler.worker = None

    rasp_aqua.scheduler.should_terminate.clear()

    my_lib.rpi.gpio.cleanup()
