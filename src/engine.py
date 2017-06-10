
import re
import itertools

import logger
from utils import *


class Rule:
    """
    Rule for name identification and renaming.
    """

    def __init__(self, identify:str, rename: str):
        self.identifier = re.compile(identify)
        self.renamer = rename

    def is_applying(self, path: str):
        return self.identifier.match(path)


class Rules:
    """
    Dataset of all rules.
    """

    def __init__(self):
        # list of Rule
        self.rules = []


    def add(self, id_rule: str, rename_rule: str):
        logger.debug("Add a rule: '{}' '{}'".format(id_rule, rename_rule))
        rule = Rule(re.compile(id_rule), rename_rule)
        self.rules.append(rule)


    @property
    def as_plain_text(self):
        for rule in self.rules:
            yield (rule.identifier.pattern, rule.renamer)


    def __len__(self):
        return len(self.rules)


    def find_rule_for(self, path: str):
        return first_map(lambda r: r.is_applying(path),
                         self.rules)

