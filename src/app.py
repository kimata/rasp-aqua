#!/usr/bin/env python3
"""
水槽の自動管理を行います．

Usage:
  rasp-aqua.py [-c CONFIG] [-d]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -d                : デバッグモードで動作します．
"""

import logging
import signal

import rasp_aqua.control
import rasp_aqua.scheduler

SCHEMA_CONFIG = "config.schema"


def sig_handler(num, frame):  # noqa: ARG001
    global should_terminate

    logging.warning("receive signal %d", num)

    if num == signal.SIGTERM:
        rasp_aqua.control.term()


######################################################################
if __name__ == "__main__":
    import pathlib

    import docopt
    import my_lib.config
    import my_lib.logger

    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    debug_mode = args["-d"]

    my_lib.logger.init("hems.rasp-water", level=logging.DEBUG if debug_mode else logging.INFO)

    config = my_lib.config.load(config_file, pathlib.Path(SCHEMA_CONFIG))

    rasp_aqua.control.execute(config)

    signal.signal(signal.SIGTERM, sig_handler)
