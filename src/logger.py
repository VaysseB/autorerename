
from pathlib import Path

import logging
import logging.config


def load_debug_conf():
    import os
    return os.environ.get("DEBUG", False) in (1, "1", "True", "TRUE")


if load_debug_conf():
    logging.config.fileConfig(Path("./log_conf_dev_console.ini").resolve())


# shorthand
info =      logging.root.info
debug =     logging.root.debug
warn =      logging.root.warn
critical =  logging.root.critical
fatal =     logging.root.fatal

# define here new logging configuration
