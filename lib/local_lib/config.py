#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pathlib

import yaml

CONFIG_PATH = "config.yaml"


def abs_path(config_path=CONFIG_PATH):
    return pathlib.Path(os.getcwd(), config_path)


# NOTE: プロジェクトによって，大文字と小文字が異なるのでここで吸収する
def get_db_config(config):
    if "INFLUXDB" in config:
        return {
            "token": config["INFLUXDB"]["TOKEN"],
            "bucket": config["INFLUXDB"]["BUCKET"],
            "url": config["INFLUXDB"]["URL"],
            "org": config["INFLUXDB"]["ORG"],
        }
    else:
        return {
            "token": config["influxdb"]["token"],
            "bucket": config["influxdb"]["bucket"],
            "url": config["influxdb"]["url"],
            "org": config["influxdb"]["org"],
        }


def load(config_path=CONFIG_PATH):
    path = str(abs_path(config_path))
    with open(path, "r", encoding="utf-8") as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
        config["base_dir"] = abs_path(config_path).parent
        return config
