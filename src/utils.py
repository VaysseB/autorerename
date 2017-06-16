
import os
from pathlib import Path

import logger


def first_map(func: callable, items: iter):
    """
    Return the first result that `bool(func(elem)) is True`.
    """
    for item in items:
        res = func(item)
        if res:
            return res


def first_that(func: callable, items: iter):
    """
    Return the first element that `bool(func(elem)) is True`.
    """
    for item in items:
        if func(item):
            return item


def scan_fs(paths: (Path,), max_depth: int=-1, recursive: bool=False) -> str:
    if not recursive:
        max_depth = 0

    def scan_folder(root: Path, limit_depth: int) -> str:
        logger.debug("scan in {} (limit depth:{})".format(root, limit_depth))
        for entry in root.iterdir():
            if entry.is_dir() and limit_depth != 0:
                yield from scan_folder(entry, limit_depth-1)
            elif entry.is_file():
                yield entry

    for root in paths:
        yield from scan_folder(root, max_depth)
