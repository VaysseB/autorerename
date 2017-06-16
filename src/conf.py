
from pathlib import Path
import configparser

import logger
from utils import *


confs = (
    "./autorerename.conf.ini",
    "~/.local/share/autorerename/config.ini",
    "~/.config/autorerename/config.ini"
)
confs = tuple(Path(c).expanduser() for c in confs)


class Conf:
    def __init__(self):
        self.path = None
        self.dbpath = None
        self.trpath = None


def abspath_from_conf(cfpath: Path, path: Path):
    return (path
            if path.is_absolute()
            else cfpath.parent.joinpath(path)).resolve()


def load_conf(cfpath: Path):
    logger.info("load config file {}".format(cfpath))
    if not cfpath:
        return Conf()

    conf = Conf()
    conf.path = cfpath

    config = configparser.ConfigParser()
    with open(cfpath, "r") as input_:
        config.read_file(input_)

    # take content from file
    dbpath = config["DEFAULT"].get("rules_db")
    if dbpath:
        conf.dbpath = abspath_from_conf(cfpath, Path(dbpath))

    return conf


def default_conf():
    path = first_that(Path.exists, confs)
    logger.info("default conf at {}".format(path))
    return load_conf(path)
