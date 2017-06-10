
import argparse

import logger
import engine
import well
from utils import *


EXIT_ERROR = 1


class App:
    def __init__(self):
        self.rules = None
        self.path = None

    def load_rules(self, filepath: str):
        self.path = filepath
        self.rules = well.load_rules(filepath)

    def save_rules(self):
        well.save_rules(self.path, self.rules)


class Args:

    def __init__(self, name=None, args=None):
        self.app = App()

        import sys
        self.prog_name = (argparse.ArgumentParser().prog
                          if name is None
                          else name)
        self.args = list((sys.argv[1:] if args is None else args)[:])
        logger.info("cmd args: %s", " ".join(self.args))


    def main(self):
        modes = {
            "rule": self.rules,
            "test": self.test_rules,
            "scan": self.scan_path
        }

        parser = argparse.ArgumentParser(
            description="TODO",
            prog=self.prog_name
        )
        parser.add_argument("mode", choices=modes.keys(),
                            help="Mode to use")
        args = parser.parse_args(self.args[0:1])

        self.prog_name += " " + args.mode
        return modes[args.mode]()


    def scan_path(self):
        parser = argparse.ArgumentParser(
            description="Scan path",
            prog=self.prog_name
        )
        parser.add_argument("--database", help="database to store rule",
                            metavar="path")
        parser.add_argument("--max-depth", type=int, default=-1,
                            help="maximum depth to scan",
                            metavar="d")
        parser.add_argument("-r", "--recursive", action="store_true",
                            help="scan recursively")
        parser.add_argument("--rule", help="id or surname of a rule")
        parser.add_argument("paths", help="file or folder", metavar="path",
                            nargs="*")
        args = parser.parse_args(self.args[1:])

        logger.info("action: scan")
        self.app.load_rules(args.database)
        counter = 0
        files_counter = 0
        args.paths = args.paths if args.paths else (".",)
        for entry in scan_fs(args.paths, max_depth=args.max_depth,
                             recursive=args.recursive):
            prev_counter = counter

            for (rule, match) in self.app.rules.find_applying(entry, args.rule):
                counter += 1
                if rule.surname:
                    print("{}:{}: {}".format(rule.guid, rule.surname,
                                             rule.format(match)))
                else:
                    print("{}: {}".format(rule.guid, rule.format(match)))

            if prev_counter != counter:
                files_counter += 1

        logger.info("Scan and tested on {} files, {} matches"
                    .format(files_counter, counter))
        print("Files: {}".format(files_counter))
        print("Count: {}".format(counter))


    def test_rules(self):
        parser = argparse.ArgumentParser(
            description="Find and test rules applying",
            prog=self.prog_name
        )
        parser.add_argument("--database", help="database to store rule",
                            metavar="path")
        parser.add_argument("--rule", help="id or surname of a rule")
        parser.add_argument("entry", help="entry to test")
        args = parser.parse_args(self.args[1:])

        logger.info("action: test")
        self.app.load_rules(args.database)
        counter = 0
        for (rule, match) in self.app.rules.find_applying(args.entry,
                                                          args.rule):
            counter += 1
            if rule.surname:
                print("{}:{}: {}".format(rule.guid, rule.surname,
                                         rule.format(match)))
            else:
                print("{}: {}".format(rule.guid, rule.format(match)))

        logger.info("Found and tested on {} rules".format(counter))
        print("Count: {}".format(counter))


    def rules(self):
        actions = {
            "add": self.rules_add,
            "list": self.rules_list,
            "remove": self.rules_remove
        }

        parser = argparse.ArgumentParser(
            description="Manage rules",
            prog=self.prog_name
        )
        parser.add_argument("action", choices=actions.keys())
        args = parser.parse_args(self.args[1:2])

        self.prog_name += " " + args.action
        return actions[args.action]()


    def rules_add(self):
        parser = argparse.ArgumentParser(
            description="Add a rule",
            prog=self.prog_name
        )
        parser.add_argument("--database", help="database to store rule",
                            metavar="path")
        parser.add_argument("id_rule",
                            help="regular expression to identify filename")
        parser.add_argument("rename_rule",
                            help="format rule to rename filename")
        parser.add_argument("surname",
                            nargs="?",
                            help="surname of the rule")
        args = parser.parse_args(self.args[2:])

        logger.info("action: add a rule")
        self.app.load_rules(args.database)
        self.app.rules.add(id_rule=args.id_rule,
                           rename_rule=args.rename_rule,
                           surname=args.surname)
        self.app.save_rules()


    def rules_list(self):
        parser = argparse.ArgumentParser(
            description="List rules",
            prog=self.prog_name
        )
        parser.add_argument("--database", help="database to store rule",
                            metavar="path")
        args = parser.parse_args(self.args[2:])

        logger.info("action: list rules")
        self.app.load_rules(args.database)
        print("Count: {}".format(len(self.app.rules)))
        for rule in self.app.rules:
            print("Rule {}".format(rule.inline()))


    def rules_remove(self):
        parser = argparse.ArgumentParser(
            description="Remove a rule",
            prog=self.prog_name
        )
        parser.add_argument("rule_id", help="unique id of the rule")
        parser.add_argument("--database", help="database to store rule",
                            metavar="path")
        args = parser.parse_args(self.args[2:])

        logger.info("action: remove rule")
        self.app.load_rules(args.database)
        if not self.app.rules.remove(args.rule_id):
            return EXIT_ERROR
        self.app.save_rules()


if __name__ == "__main__":
    ret = Args().main()
    exit(0 if ret is None else ret)
