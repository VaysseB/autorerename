
"""
Load and Save functionalities.

It drops and pulls from the well.
"""

from pathlib import Path
import pickle

import logger
import engine


def serialize_rule(rule: engine.Rule) -> dict:
    return {
        "guid": rule.guid,
        "id": rule.identifier_as_text,
        "rn": rule.renamer_as_text,
        "name": rule.name
    }


def deserialize_rule(rules: engine.Rules, data: dict) -> engine.Rule:
    return rules.add(
        id_rule=data["id"],
        rename_rule=data["rn"],
        guid=data["guid"],
        name=data["name"]
    )


def save_rules(path: Path, rules: engine.Rules):
    """
    Save rules to file.
    """
    logger.info("Saving rules to %s", path)
    with open(path, "wb") as output:
        writer = pickle.Pickler(output, pickle.DEFAULT_PROTOCOL)
        writer.dump({
            "version": 1,
            "rules": tuple(serialize_rule(r) for r in rules)
        })
    logger.info("Rules saved.")


def load_rules(path: Path) -> engine.Rules:
    """
    Load rules from file.
    """
    rules = engine.Rules()

    logger.info("Loading rules from %s", path)

    if path is None:
        return rules
    elif not path.exists():
        logger.info("database path doesn't exists {}".format(path))
        return rules
    # special cases for pickle if input is empty
    elif path.stat().st_size <= 0:
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

        for data in data.get("rules", ()):
            deserialize_rule(rules, data)

        logger.info("Loaded %d rules", len(rules))

    return rules


