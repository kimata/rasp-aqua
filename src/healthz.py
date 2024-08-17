#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liveness のチェックを行います

Usage:
  healthz.py [-c CONFIG] [-d]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -d                : デバッグモードで動作します．
"""

import datetime
import logging
import pathlib
import sys


def check_liveness(config):
    liveness_file = pathlib.Path(config["liveness"]["file"]["scheduler"])
    interval_sec = config["liveness"]["interval_sec"]

    if not liveness_file.exists():
        logging.warning("Not executed.")
        return False

    elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(liveness_file.stat().st_mtime)
    # NOTE: 少なくとも1分は様子を見る
    if elapsed.total_seconds() > max(interval_sec * 2, 60):
        logging.warning(
            "Execution interval is too long. ({elapsed:,} sec)".format(elapsed=elapsed.total_seconds)
        )
        return False

    return True


######################################################################
if __name__ == "__main__":
    from docopt import docopt

    import local_lib.logger
    import local_lib.config

    args = docopt(__doc__)

    config_file = args["-c"]
    debug_mode = args["-d"]

    if debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    local_lib.logger.init("hems.rasp-aqua", level=log_level)

    logging.info("Using config config: {config_file}".format(config_file=config_file))
    config = local_lib.config.load(config_file)

    if check_liveness(config):
        logging.info("OK.")
        sys.exit(0)
    else:
        sys.exit(-1)
