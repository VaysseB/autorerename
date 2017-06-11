
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
        writer.dump({"version": 1, "rules": tuple(rules.as_plain)})
    logger.info("Rules saved.")


def load_rules(path: str) -> engine.Rules:
    """
    Load rules from file.
    """
    rules = engine.Rules()

    logger.info("Loading rules from %s", path)

    if path is None:
        return rules
    elif not os.path.exists(path):
        logger.info("database path doesn't exists {}".format(path))
        return rules
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

        for thing in data.get("rules", ()):
            rules.add(id_rule=thing["id"],
                      rename_rule=thing["ft"],
                      guid=thing["guid"],
                      surname=thing["snm"],
                      match_fullpath=thing["fullpath"])

        logger.info("Loaded %d rules", len(rules))

    return rules


def save_training(path: str, training: engine.Training):
    """
    Save training dataset to file.
    """
    logger.info("Saving training dataset to %s", path)
    with open(path, "wb") as output:
        writer = pickle.Pickler(output, pickle.DEFAULT_PROTOCOL)
        writer.dump({"version": 1, "material": training.material})
    logger.info("Training dataset saved.")


def load_training(path: str) -> engine.Training:
    """
    Load training dataset from file.
    """
    training = engine.Training()

    logger.info("Loading training dataset from %s", path)

    if path is None:
        return training
    elif not os.path.exists(path):
        logger.info("database path doesn't exists {}".format(path))
        return training
    # special cases for pickle if input is empty
    elif os.path.getsize(path) <= 0:
        logger.info("empty database")
        return training

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

        training.material = data.get("material", {})
        logger.info("Loaded %d training dataset", len(training))

    return training


