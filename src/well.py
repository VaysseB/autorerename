
"""
Load and Save functionalities.

It drops and pulls from the well.
"""


import pickle

import logger
import engine


def save_rules(path: str, rules: engine.Rules):
    """
    Save rules to file.
    """
    logger.info("Saving rules to %s", path)
    with open(path, "wb", encoding="utf-8") as output:
        writer = pickle.Pickler(output, pickle.DEFAULT_PROTOCOL)
        writer.dump({"version": 1, "rules": rules.as_plain_text})
    logger.info("Rules saved.")


def load_rules(path: str) -> engine.Rules:
    """
    Load rules from file.
    """
    rules = engine.Rules()

    logger.info("Loading rules from %s", path)
    with open(path, "rb", encoding="utf-8") as input:
        reader = pickle.Pickler(input, pickle.DEFAULT_PROTOCOL,
                                encoding="utf-8")
        data = reader.load()
        if not data or not isinstance(data, dict):
            logger.critical("data loaded isn't what expected")
            raise RuntimeError("invalid data from file")

        version = data.get("version", None)
        if version != 1:
            logger.warn("cannot load file with version %d", version)
            raise RuntimeError("cannot load data from version {}"
                               .format(version))

        for thing in data.get("rules", ()):
            rules.add(thing)

        logger.info("Loaded %d rules", len(rules))

    return rules

