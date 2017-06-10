
import re
import itertools
import hashlib
import datetime

import logger
from utils import *


class Rule:
    """
    Rule for name identification and renaming.
    """

    def __init__(self, identify:str, rename: str, guid=None):
        self.identifier = re.compile(identify)
        self.renamer = rename
        self.guid = guid

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.guid == other.guid
        return False

    def __hash__(self):
        return hash(self.guid)

    def is_applying(self, path: str):
        return self.identifier.match(path)

    def format(self, match: re.match):
        groups = {name: match.group(name) for name in match.groups()}
        return self.renamer.format(**groups)

    @property
    def as_dict(self):
        return {"guid": self.guid, "id": self.identifier.pattern, "ft": self.renamer}


class Rules:
    """
    Dataset of all rules.
    """

    def __init__(self):
        # list of Rule
        self.rules = {}


    def add(self, id_rule: str, rename_rule: str, guid=None) -> bool:
        logger.debug("Add rule {}: '{}' '{}'".format(guid, id_rule, rename_rule))
        rule = Rule(re.compile(id_rule), rename_rule)

        if guid is None:
            while guid is None or guid in self.rules:
                m = hashlib.sha1()
                m.update(id_rule.encode("utf8"))
                m.update(rename_rule.encode("utf8"))
                m.update(datetime.datetime.today().isoformat().encode("utf8"))
                guid = m.hexdigest()[:12]
            logger.debug("create id '{}' for rule".format(guid))
        elif guid in self.rules:
            logger.debug("already existing rule {}: {} {}"
                         .format(guid, id_rule, rename_rule))
            return False

        rule.guid = guid
        self.rules[guid] = rule
        return True


    def remove(self, guid) -> bool:
        logger.debug("Remove rule {}".format(guid))
        rule = self.rules.pop(guid, None)

        if rule is None:
            logger.debug("No such rule {}".format(guid))
            return False

        logger.debug("Found rule {}: {} {}".format(guid,
                                                   rule.identifier.pattern,
                                                   rule.renamer))
        return True


    def find_applying(self, path: str) -> ((Rule, re.match)):
        for rule in self.rules.values():
            match = rule.identifier.match(path)
            if match:
                yield (rule, match)


    @property
    def as_plain_text(self):
        for rule in self.rules.values():
            yield rule.as_dict


    def __len__(self):
        return len(self.rules)


    def find_rule_for(self, path: str):
        return first_map(lambda r: r.is_applying(path),
                         self.rules.values())

