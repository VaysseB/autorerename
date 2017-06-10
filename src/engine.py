
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
        self.surname = None

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.guid == other.guid
        return False

    def __hash__(self):
        return hash(self.guid)

    def match(self, path: str):
        return self.identifier.match(path)

    def format(self, match: re.match):
        return self.renamer.format(None, *match.groups(), **match.groupdict())

    @property
    def as_dict(self):
        return {"guid": self.guid, "id": self.identifier.pattern,
                "ft": self.renamer, "snm": self.surname}

    def inline(self) -> str:
        text = "{}: {} -> {}".format(self.guid,
                                     self.identifier.pattern,
                                     self.renamer)
        if self.surname:
            text += " [" + self.surname + "]"
        return text


class Rules:
    """
    Dataset of all rules.
    """

    def __init__(self):
        # list of Rule
        self.rules = {}

    def add(self, id_rule: str, rename_rule: str, guid=None, surname: str=None) -> bool:
        rule = Rule(re.compile(id_rule), rename_rule)
        rule.surname = surname
        rule.guid = guid
        logger.debug("Add rule {}".format(rule.inline()))

        if guid is None:
            while guid is None or guid in self.rules:
                m = hashlib.sha1()
                m.update(id_rule.encode("utf8"))
                m.update(rename_rule.encode("utf8"))
                m.update(datetime.datetime.today().isoformat().encode("utf8"))
                guid = m.hexdigest()[:12]
            rule.guid = guid
            logger.debug("create id '{}' for rule".format(guid))
        elif guid in self.rules:
            logger.debug("already existing rule {}", rule.inline())
            return False

        self.rules[rule.guid] = rule
        return True

    def remove(self, guid) -> bool:
        logger.debug("Remove rule {}".format(guid))
        rule = self.rules.pop(guid, None)

        if rule is None:
            logger.debug("No such rule {}".format(guid))
            return False

        logger.debug("Found rule {}".format(rule.inline()))
        return True

    def find_applying(self, path: str, surname: str=None) -> ((Rule, re.match)):
        items = iter(self.rules.values())
        if surname:
            items = filter(lambda r: r.surname == surname, items)

        for rule in items:
            match = rule.match(path)
            if match:
                yield (rule, match)

    @property
    def as_plain_text(self):
        for rule in self.rules.values():
            yield rule.as_dict

    def __len__(self):
        return len(self.rules)

    def __iter__(self) -> Rule:
        return iter(self.rules.values())

    def find_rule_for(self, path: str):
        return first_map(lambda r: r.match(path),
                         self.rules.values())
