
"""
Load and Save functionalities.

It drops and pulls from the well.
"""

import os.path
import pickle

import logger
import engine


def save_rules(path: str, rules: engine.Rules):
    """
    Save rules to file.
    """
    logger.info("Saving rules to %s", path)
    with open(path, "wb") as output:
        writer = pickle.Pickler(output, pickle.DEFAULT_PROTOCOL)
        writer.dump({"version": 1, "rules": tuple(rules.as_plain_text)})
    logger.info("Rules saved.")


def load_rules(path: str) -> engine.Rules:
    """
    Load rules from file.
    """
    rules = engine.Rules()

    logger.info("Loading rules from %s", path)

    if not os.path.exists(path):
        logger.info("database path doesn't exists {}".format(path))
        raise RuntimeError("invalid path {}".format(path))
    # special cases for pickle if input is empty
    elif os.path.getsize(path) <= 0:
        logger.info("empty database")
        return rules

    with open(path, "rb") as input_:
        reader = pickle.Unpickler(input_)

        data = reader.load()
        if not data or not isinstance(data, dict):
            logger.critical("data loaded isn't what expected")
            raise RuntimeError("invalid data from file")

        version = data.get("version", None)
        if version != 1:
            logger.warn("cannot load file with version %d", version)
            raise RuntimeError("cannot load data from version {}"
                               .format(version))

        for (a, b) in data.get("rules", ()):
            rules.add(a, b)

        logger.info("Loaded %d rules", len(rules))

    return rules

