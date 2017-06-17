
from pathlib import Path
import configparser

import logger
from utils import *


# compatibility with 3.4
if not hasattr(Path, "expanduser"):
    import os.path
    def expanduser(self):
        return os.path.expanduser(str(self))
    Path.expanduser = expanduser


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
        self.actlog_path = None


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

    # take action log from file
    action_log_path = config["DEFAULT"].get("action_log")
    if action_log_path:
        conf.actlog_path = abspath_from_conf(cfpath, Path(action_log_path))

    return conf


def default_conf():
    path = first_that(Path.exists, confs)
    logger.info("default conf at {}".format(path))
    return load_conf(path)
