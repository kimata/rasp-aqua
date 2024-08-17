#!/usr/bin/env python3
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
import traceback

import schedule

worker = None
should_terminate = False
executed_job = False


def init(timezone, queue, liveness_file, check_interval_sec):
    global worker  # noqa: PLW0603

    worker = threading.Thread(
        target=schedule_worker,
        args=(timezone, queue, liveness_file, check_interval_sec),
    )

    worker.start()


def schedule_task(*args, **kwargs):
    global executed_job  # noqa: PLW0603

    func = args[0]

    logging.info(
        "Execute %s (%s:%s)", kwargs["name"], pathlib.Path(func.__code__.co_filename).name, func.__name__
    )

    func(*args[1:])

    executed_job = True


def schedule_status():
    for job in sorted(schedule.get_jobs(), key=lambda job: job.next_run):
        logging.info("Next run of %s: %s", job.job_func.keywords["name"], job.next_run)

    idle_sec = schedule.idle_seconds()
    if idle_sec is not None:
        logging.info("Time to next jobs is %.1f sec", idle_sec)


def set_schedule(timezone, schedule_data):
    schedule.clear()

    for entry in schedule_data:
        args = (entry["func"],) + entry["args"]
        schedule.every().day.at(entry["time"], timezone).do(schedule_task, *args, name=entry["name"])


def schedule_worker(timezone, queue, liveness_path, check_interval_sec):
    global should_terminate
    global executed_job  # noqa: PLW0603

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
                schedule_status()

            schedule.run_pending()

            if executed_job:
                schedule_status()
                executed_job = False

            sleep_sec = max(check_interval_sec - (time.time() - time_start), 1)
            logging.debug("Sleep %.1f sec...", sleep_sec)
            time.sleep(sleep_sec)
        except OverflowError:  # pragma: no cover
            # NOTE: テストする際，freezer 使って日付をいじるとこの例外が発生する
            logging.debug(traceback.format_exc())

        # NOTE: 10秒以上経過していたら，liveness を更新する
        if (check_interval_sec >= 10) or (i % (10 / check_interval_sec) == 0):
            liveness_file.touch()
        i += 1

    logging.info("Terminate schedule worker")
