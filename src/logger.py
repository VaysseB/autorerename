
def local_path(filename: str):
    import os.path
    this_file = os.path.abspath(os.path.realpath(__file__))
    root_dir = os.path.dirname(this_file)
    return os.path.join(root_dir, filename)


def load_debug_conf():
    import os
    return os.environ.get("DEBUG", False) in (1, "1", "True", "TRUE")


import logging
import logging.config

if load_debug_conf():
    logging.config.fileConfig(local_path("./log_conf_dev_console.ini"))

# shorthand
info =      logging.root.info
debug =     logging.root.debug
warn =      logging.root.warn
critical =  logging.root.critical
fatal =     logging.root.fatal

# define here new logging configuration
