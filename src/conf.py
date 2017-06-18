
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

DEFAULT_RULE_DB_PATH = Path(".priv/rules")
DEFAULT_ACTION_LOG_PATH = Path(".priv/action_log")


class Conf:
    def __init__(self):
        self.path = None
        self.rule_db_path = DEFAULT_RULE_DB_PATH
        self.actlog_path = DEFAULT_ACTION_LOG_PATH


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
    db_path = config["DEFAULT"].get("rules_db",
                                    fallback=conf.rule_db_path)
    conf.rule_db_path = abspath_from_conf(cf_path, Path(db_path))

    # take action log from file
    actlog_path = config["DEFAULT"].get("action_log",
                                        fallback=conf.actlog_path)
    conf.actlog_path = abspath_from_conf(cf_path, Path(actlog_path))

    return conf


def default_conf():
    path = first_that(Path.exists, confs)
    logger.info("default conf at {}".format(path))
    return load_conf(path)


def save_conf(conf: Conf):
    config = configparser.ConfigParser()
    config["DEFAULT"]["rules_db"] = str(conf.rule_db_path)
    config["DEFAULT"]["action_log"] = str(conf.actlog_path)

    with open(str(conf.path), "w") as output:
        config.write(output)
