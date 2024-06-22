#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
関数を指定時刻に呼び出します．

Usage:
  scheduler.py [-c CONFIG]

Options:
  -c CONFIG     : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

import logging
import pathlib
import threading
import time
import datetime
import traceback
import schedule

schedule_lock = None
should_terminate = False


def init():
    global schedule_lock
    schedule_lock = threading.Lock()


def set_schedule(timezone, schedule_data):
    schedule.clear()

    for entry in schedule_data:
        logging.info(entry)
        schedule.every().day.at(entry["time"], timezone).do(entry["func"], *entry["args"])

    for job in schedule.get_jobs():
        logging.info("Next run: {next_run}".format(next_run=job.next_run))

    idle_sec = schedule.idle_seconds()
    logging.info("Time to next jobs is {idle:.1f} sec".format(idle=idle_sec))


def schedule_worker(timezone, queue, liveness_path, check_interval_sec=10):
    global should_terminate

    liveness_file = pathlib.Path(liveness_path)
    liveness_file.parent.mkdir(parents=True, exist_ok=True)

    logging.info("Start schedule worker")

    i = 0
    while True:
        if should_terminate:
            break
        try:
            time_start = time.time()
            if not queue.empty():
                schedule_data = queue.get()
                set_schedule(timezone, schedule_data)

            schedule.run_pending()

            sleep_sec = max(check_interval_sec - (time.time() - time_start), 1)
            logging.debug("Sleep {sleep_sec:.1f} sec...".format(sleep_sec=sleep_sec))
            time.sleep(sleep_sec)
        except OverflowError:  # pragma: no cover
            # NOTE: テストする際，freezer 使って日付をいじるとこの例外が発生する
            logging.debug(traceback.format_exc())
            pass

        # NOTE: 10秒以上経過していたら，liveness を更新する
        if (check_interval_sec >= 10) or (i % (10 / check_interval_sec) == 0):
            liveness_file.touch()
        i += 1

    logging.info("Terminate schedule worker")


if __name__ == "__main__":
    from docopt import docopt
    from multiprocessing import Queue
    from multiprocessing.pool import ThreadPool
    import pytz

    import local_lib.logger
    import local_lib.config
    import aquarium.valve

    args = docopt(__doc__)

    local_lib.logger.init("test", level=logging.DEBUG)

    config = local_lib.config.load(args["-c"])

    aquarium.valve.init()

    queue = Queue()
    pool = ThreadPool(processes=1)
    timezone = pytz.timezone("Asia/Tokyo")

    result = pool.apply_async(schedule_worker, (timezone, queue, config["liveness"]["file"]["scheduler"]))

    exec_time = datetime.datetime.now(timezone) + datetime.timedelta(minutes=1)
    queue.put(
        [
            {
                "time": exec_time.strftime("%H:%M"),
                "func": aquarium.valve.control,
                "args": (aquarium.valve.MODE.CO2,),
            }
        ]
    )

    # NOTE: 終了するのを待つ
    result.get()
