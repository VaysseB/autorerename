
"""
Load and Save functionalities.

It drops and pulls from the well.
"""

from pathlib import Path
import pickle

import logger
import book


def serialize_rule(rule: book.Rule) -> dict:
    return {
        "guid": str(rule.guid),
        "id": str(rule.identifier_as_text),
        "rn": str(rule.renamer_as_text),
        "name": str(rule.name) if rule.name else None,
        "height": int(rule.height)
    }


def deserialize_rule(rules: book.Rules, data: dict) -> book.Rule:
    return rules.add(
        id_rule=data["id"],
        rename_rule=data["rn"],
        guid=data["guid"],
        name=data["name"],
        height=data["height"]
    )


def save_rules(path: Path, rules: book.Rules):
    """
    Save rules to file.
    """
    logger.info("Saving rules to %s", path)
    with open(str(path), "wb") as output:
        writer = pickle.Pickler(output, pickle.DEFAULT_PROTOCOL)
        writer.dump({
            "version": 1,
            "rules": tuple(serialize_rule(r) for r in rules)
        })
    logger.info("Rules saved.")


def load_rules(path: Path) -> book.Rules:
    """
    Load rules from file.
    """
    rules = book.Rules()

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

    with open(str(path), "rb") as input_:
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


