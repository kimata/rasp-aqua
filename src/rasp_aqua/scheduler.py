#!/usr/bin/env python3
"""
関数を指定時刻に呼び出します．

Usage:
  scheduler.py [-c CONFIG]

Options:
  -c CONFIG     : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

import datetime
import logging
import pathlib
import threading
import time
import traceback

import my_lib.footprint
import pytz
import schedule

worker = None
should_terminate = threading.Event()
executed_job = False

timezone = None


def init(timezone_, queue, liveness_file, check_interval_sec):
    global worker  # noqa: PLW0603
    global timezone  # noqa: PLW0603

    timezone = timezone_

    worker = threading.Thread(
        target=schedule_worker,
        args=(queue, liveness_file, check_interval_sec),
    )

    worker.start()


def schedule_task(*args, **kwargs):
    global executed_job  # noqa: PLW0603
    global timezone

    func = args[0]

    logging.info(
        "Now is %s",
        datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=timezone["offset"]))).strftime(
            "%Y-%m-%d %H:%M"
        ),
    )
    logging.info(
        "Execute %s (%s:%s)", kwargs["name"], pathlib.Path(func.__code__.co_filename).name, func.__name__
    )

    func(*args[1:])

    executed_job = True


def schedule_status():
    global timezone

    for job in sorted(schedule.get_jobs(), key=lambda job: job.next_run):
        logging.info("Schedule run of %-7s: %s", job.job_func.keywords["name"], job.next_run)

    idle_sec = schedule.idle_seconds()
    if idle_sec is not None:
        hours, remainder = divmod(idle_sec, 3600)
        minutes, seconds = divmod(remainder, 60)

        logging.info(
            "Now is %s, time to next jobs is %d hour(s) %d minute(s) %d second(s)",
            datetime.datetime.now(
                tz=datetime.timezone(datetime.timedelta(hours=timezone["offset"]))
            ).strftime("%Y-%m-%d %H:%M"),
            hours,
            minutes,
            seconds,
        )


def set_schedule(schedule_data):
    global timezone

    schedule.clear()

    for entry in schedule_data:
        args = (entry["func"],) + entry["args"]
        schedule.every().day.at(entry["time"], pytz.timezone(timezone["zone"])).do(
            schedule_task, *args, name=entry["name"]
        )


def schedule_worker(queue, liveness_file, check_interval_sec):
    global should_terminate
    global executed_job  # noqa: PLW0603

    logging.info("Start schedule worker")

    i = 0
    while True:
        if should_terminate.is_set():
            schedule.clear()
            break
        try:
            time_start = time.time()
            while not queue.empty():
                logging.debug("Regist scheduled job")
                schedule_data = queue.get()
                set_schedule(schedule_data)
                schedule_status()

            schedule.run_pending()

            if executed_job:
                schedule_status()
                executed_job = False

            sleep_sec = max(check_interval_sec - (time.time() - time_start), 0.1)
            logging.debug("Sleep %.1f sec...", sleep_sec)
            time.sleep(sleep_sec)
        except OverflowError:  # pragma: no cover
            # NOTE: テストする際，freezer 使って日付をいじるとこの例外が発生する
            logging.debug(traceback.format_exc())

        # NOTE: 10秒以上経過していたら，liveness を更新する
        if (check_interval_sec >= 10) or (i % (10 / check_interval_sec) == 0):
            my_lib.footprint.update(liveness_file)

        i += 1

    logging.info("Terminate schedule worker")
