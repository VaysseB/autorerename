
from pathlib import Path
import configparser

import logger
from utils import *


# compatibility with 3.4
if not hasattr(Path, "expanduser"):
    import os.path
    def expanduser(self) -> Path:
        return Path(os.path.expanduser(str(self)))
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
        self.rule_db_path = None
        self.actlog_path = None


def abspath_from_conf(cf_path: Path, path: Path):
    return (path
            if path.is_absolute()
            else cf_path.parent.joinpath(path)).resolve()


def load_conf(cf_path: Path):
    logger.info("load config file {}".format(cf_path))
    if not cf_path:
        return Conf()

    conf = Conf()
    conf.path = cf_path

    config = configparser.ConfigParser()
    with open(str(cf_path), "r") as input_:
        config.read_file(input_)

    # take content from file
    db_path = config["DEFAULT"].get("rules_db")
    if not db_path:
        db_path = "rules.pickle"
    conf.rule_db_path = abspath_from_conf(cf_path, Path(db_path))

    # take action log from file
    actlog_path = config["DEFAULT"].get("action_log")
    if not actlog_path:
        actlog_path = "actlog.pickle"
    conf.actlog_path = abspath_from_conf(cf_path, Path(actlog_path))

    return conf


def default_conf():
    path = first_that(Path.exists, confs)
    logger.info("default conf at {}".format(path))
    return load_conf(path)
