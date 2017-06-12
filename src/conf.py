
import os.path
import configparser

import logger
from utils import *


confs = (
    "./autorerename.conf.ini",
    "~/.local/share/autorerename/config.ini",
    "~/.config/autorerename/config.ini"
)
confs = tuple(os.path.realpath(os.path.expanduser(p)) for p in confs)


class Conf:
    def __init__(self):
        self.path = None
        self.dbpath = None
        self.trpath = None


def abspath_from_conf(cfpath:str, path: str):
    root = os.path.dirname(os.path.abspath(cfpath))
    path = os.path.expanduser(path)
    if os.path.isabs(path):
        return path
    return os.path.join(root, path)


def load_conf(cfpath: str):
    logger.info("load config file {}".format(cfpath))
    if not cfpath:
        return Conf()

    cfpath = os.path.abspath(cfpath)

    conf = Conf()
    conf.path = cfpath

    config = configparser.ConfigParser()
    with open(cfpath, "r") as input_:
        config.read_file(input_)

    # take content from file
    dbpath = config["DEFAULT"].get("rules_db")
    if dbpath:
        conf.dbpath = abspath_from_conf(cfpath, dbpath)

    return conf


def default_conf():
    path = first_that(os.path.exists, confs)
    logger.info("default conf at {}".format(path))
    return load_conf(path)
