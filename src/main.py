
import argparse

import logger
import engine
import well
import conf
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


class RuleCommands:
    def __init__(self, config: conf.Conf):
        self.config = config

    def add(self, args):
        logger.info("action: add a rule")

        app = App()
        app.load_rules(args.dbpath)

        app.rules.add(id_rule=args.id_rule,
                      rename_rule=args.rename_rule,
                      surname=args.surname)
        app.save_rules()


    def list(self, args):
        logger.info("action: list rules")

        app = App()
        app.load_rules(args.dbpath)

        for rule in app.rules:
            print("Rule {}".format(rule.inline()))


    def remove(self, args):
        logger.info("action: remove rule")

        app = App()
        app.load_rules(args.dbpath)

        if not app.rules.remove(args.rule_id):
            return EXIT_ERROR
        app.save_rules()


    def test(self, args):
        logger.info("action: test")

        app = App()
        app.load_rules(args.dbpath)

        counter = 0
        for (rule, match) in app.rules.find_applying(args.entry, args.rule):
            counter += 1
            if rule.surname:
                print("{}:{}: {}".format(rule.guid,
                                         rule.surname,
                                         rule.format(match)))
            else:
                print("{}: {}".format(rule.guid,
                                      rule.format(match)))

        logger.info("Found and tested on {} rules".format(counter))


class FolderCommands:
    def __init__(self, config: conf.Conf):
        self.config = config

    def scan(self, args):
        logger.info("action: scan")

        app = App()
        app.load_rules(args.dbpath)

        counter = 0
        files_counter = 0
        for entry in scan_fs(args.paths, max_depth=args.max_depth,
                             recursive=args.recursive):
            prev_counter = counter

            for (rule, match) in app.rules.find_applying(entry, args.rule):
                counter += 1
                header = rule.guid + ":" + (
                    (rule.surname + ":") if rule.surname else "")
                new_path = rule.format(match)
                print(header, entry, " --> ", new_path)

            if prev_counter != counter:
                files_counter += 1

        logger.info("Scan and tested on {} files, {} matches"
                    .format(files_counter, counter))
        if files_counter > 0:
            print("Files: {}".format(files_counter))


class Args:
    def __init__(self):
        self.config = None

    def main(self):
        parser = argparse.ArgumentParser(
            description="File identification and rename action."
        )
        subparsers = parser.add_subparsers(
            title="mode",
            dest="mode",
            help="Mode to use")
        self.install_scan_path(subparsers)
        self.install_test_rules(subparsers)
        rule_parser = self.install_rules(subparsers)

        args = parser.parse_args()
        self.resolve(args,
                     parser.print_help,
                     rule_parser.print_help)


    def resolve(self, args, mode_help, rule_help):
        # TODO if we can specify the config file in arguments, loads it here
        self.config = conf.default_conf()

        rc = RuleCommands(self.config)
        fc = FolderCommands(self.config)

        action = {
            "_key": "mode",
            "_help": mode_help,
            "scan": fc.scan,
            "test": rc.test,
            "rule": {
                "_key": "action",
                "_help": rule_help,
                "add": rc.add,
                "list": rc.list,
                "remove": rc.remove
            }
        }

        while not callable(action) and action is not None:
            key = action["_key"]
            help = lambda _, f=action["_help"]: f()
            next = getattr(args, key)
            action = action.get(next, help)

        #
        self._found_db(args)
        action(args)


    def _add_db(self, parser, depth: int):
        """
        Insert the database parse option into the give parser.
        """
        parser.add_argument("--database",
                            help="database of rules",
                            metavar="path",
                            dest="dbpath" + str(depth))


    def _found_db(self, args):
        """
        Find the first `dbpathX` and store it in `dbpath`.
        """
        path = None
        depth = 1
        key = "dbpath" + str(depth)
        while path is None and hasattr(args, key):
            path = getattr(args, key)
            depth += 1
            key = "dbpath" + str(depth)
        args.dbpath = path

        # if database not given, get them from configuration file
        if path is None:
            args.dbpath = self.config.dbpath


    def install_scan_path(self, subparser):
        parser = subparser.add_parser(
            "scan",
            help="Scan path for rule application."
        )
        self._add_db(parser, depth=1)
        parser.add_argument("--max-depth",
                            type=int,
                            default=-1,
                            help="maximum depth to scan",
                            metavar="d")
        parser.add_argument("-r", "--recursive",
                            action="store_true",
                            help="scan recursively")
        parser.add_argument("--rule",
                            help="id or surname of a rule",
                            metavar="r")
        parser.add_argument("paths",
                            help="file or folder",
                            metavar="path",
                            nargs="*",
                            default=(".",))
        return parser


    def install_test_rules(self, subparser):
        parser = subparser.add_parser(
            "test",
            help="Find and test rules application."
        )
        self._add_db(parser, depth=1)
        parser.add_argument("--rule",
                            help="id or surname of a rule",
                            metavar="r")
        parser.add_argument("entry",
                            help="entry to test")
        return parser


    def install_rules(self, subparser):
        parser = subparser.add_parser(
            "rule",
            help="Manage rules."
        )
        self._add_db(parser, depth=1)

        subsubparser = parser.add_subparsers(
            title="action",
            dest="action",
            help="Action to do")
        self.install_add_rule(subsubparser)
        self.install_list_rules(subsubparser)
        self.install_remove_rule(subsubparser)
        return parser


    def install_add_rule(self, subparser):
        parser = subparser.add_parser(
            "add",
            help="Add a rule."
        )
        self._add_db(parser, depth=2)
        parser.add_argument("id_rule",
                            help="regular expression to identify filename")
        parser.add_argument("rename_rule",
                            help="format rule to rename filename")
        parser.add_argument("surname",
                            nargs="?",
                            help="surname of the rule")
        return parser


    def install_list_rules(self, subparser):
        parser = subparser.add_parser(
            "list",
            help="List rules."
        )
        self._add_db(parser, depth=2)
        return parser


    def install_remove_rule(self, subparser):
        parser = subparser.add_parser(
            "remove",
            help="Remove a rule."
        )
        self._add_db(parser, depth=2)
        parser.add_argument("rule_id",
                            help="unique id of the rule")
        return parser


if __name__ == "__main__":
    ret = Args().main()
    exit(0 if ret is None else ret)
