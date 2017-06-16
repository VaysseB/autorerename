
import re
import itertools
import hashlib
import datetime
from pathlib import Path

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
        self.name = None

    def name_prefix(self):
        if self.name:
            return "{}:{}".format(self.guid, self.name)
        return self.guid

    @property
    def identifier_as_text(self):
        return self.identifier.pattern

    @property
    def renamer_as_text(self):
        return self.renamer

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.guid == other.guid
        return False

    def __hash__(self):
        return hash(self.guid)

    def match(self, path: Path):
        return self.identifier.match(path.name)

    def format(self, path: Path, match: re.match):
        updated_name = self.renamer.format(None, *match.groups(), **match.groupdict())
        return path.with_name(updated_name)

    def inline(self) -> str:
        text = "{}: '{}' ==> '{}'".format(
            self.guid,
            self.identifier.pattern,
            self.renamer)
        return text


class Rules:
    """
    Dataset of all rules.
    """

    def __init__(self):
        # list of Rule
        self.rules = {}

    def add(self, id_rule: str,
            rename_rule: str,
            guid=None,
            name: str=None) -> bool:

        # create the rule
        rule = Rule(re.compile(id_rule), rename_rule)
        rule.name = name
        rule.guid = guid
        logger.info("add rule {}".format(rule.guid))

        # create guid if this is a new rule
        if guid is None:
            while guid is None or guid in self.rules:
                m = hashlib.sha1()
                m.update(id_rule.encode("utf8"))
                m.update(rename_rule.encode("utf8"))
                m.update(datetime.datetime.today().isoformat().encode("utf8"))
                guid = m.hexdigest()[:12]
            rule.guid = guid
            logger.info("create id '{}' for rule".format(guid))
        elif guid in self.rules:
            logger.warn("already existing rule {}".format(guid))
            return

        self.rules[rule.guid] = rule
        return rule

    def remove(self, guid=None, name=None) -> bool:
        logger.info("remove rule {} or {}".format(guid, name))
        rule = self.rules.pop(guid, None)

        if rule is None:
            rule = self._find_name(name)
            if rule:
                self.rules.pop(rule.guid, None)
                guid = rule.guid
            else:
                logger.warn("no such rule {}".format(guid))
                return False

        logger.info("found rule {}".format(guid))
        return True

    def find_applying(self, path: Path, name_or_id: str=None) -> ((Rule, re.match)):
        items = iter(self.rules.values())
        if name_or_id:
            items = filter(lambda r: name_or_id in (r.name, r.guid), items)

        for rule in items:
            match = rule.match(path)
            if match:
                yield (rule, path, match)

    def __len__(self):
        return len(self.rules)

    def __iter__(self) -> Rule:
        return iter(self.rules.values())

    def find_rule_for(self, path: str):
        return first_map(lambda r: r.match(path),
                         self.rules.values())

    def _find_name(self, name: str) -> Rule:
        return first_that(lambda r: r.name == name, self.rules.values())

