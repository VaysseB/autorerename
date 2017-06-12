
import os
import os.path

import logger


def first_map(func: callable, items: iter):
    """
    Return the first result that `bool(func(elem)) is True`.
    """
    for item in items:
        res = func(item)
        if bool(res) is True:
            return res


def first_that(func: callable, items: iter):
    """
    Return the first element that `bool(func(elem)) is True`.
    """
    for item in items:
        if bool(func(item)) is True:
            return item


def scan_fs(paths, max_depth: int=-1, recursive: bool=False) -> str:
    if not recursive:
        max_depth = 0

    def scan_folder(root, limit_depth: int) -> str:
        logger.debug("scan in {} (limit depth:{})".format(root, limit_depth))
        for entry in os.listdir(root):
            entry = os.path.join(root, entry)
            if os.path.isdir(entry) and limit_depth != 0:
                yield from scan_folder(entry, limit_depth-1)
            elif os.path.isfile(entry):
                yield entry

    for root in paths:
        yield from scan_folder(root, max_depth)
