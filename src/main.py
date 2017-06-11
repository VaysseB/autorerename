
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
        self.rule_path = None
        self.training = None
        self.training_path = None

    def load_rules(self, filepath: str):
        self.rule_path = filepath
        self.rules = well.load_rules(filepath)

    def save_rules(self):
        if self.rule_path:
            well.save_rules(self.rule_path, self.rules)
        else:
            logger.warn("no path of database to save rules")

    def load_training(self, filepath: str):
        self.training_path = filepath
        self.training = well.load_training(filepath)

    def save_training(self):
        if self.training_path:
            well.save_training(self.training_path, self.training)
        else:
            logger.warn("no path of database to save training dataset")


class Commands:
    def apply(self, rules: engine.Rules, entry: str, rule_id_or_name: str=None) -> int:
        counter = 0
        for (rule, entry, match) in rules.find_applying(entry, rule_id_or_name):
            counter += 1
            text = rule.name_prefix()
            result = rule.format(entry, match)
            print("{}: '{}' --> '{}'".format(text, entry, result))
        return counter


class RuleCommands(Commands):
    def __init__(self, config: conf.Conf):
        self.config = config


    def _add_rule(self, rules: engine.Rules, args):
        rule = rules.add(
            id_rule=args.id_rule,
            rename_rule=args.rename_rule,
            surname=getattr(args, "surname", None),
            match_fullpath=getattr(args, "fullpath", False))
        return rule


    def add(self, args):
        logger.info("action: add a rule")

        app = App()
        app.load_rules(args.dbpath)
        self._add_rule(app.rules, args)
        app.save_rules()


    def list(self, args):
        logger.info("action: list rules")

        app = App()
        app.load_rules(args.dbpath)

        for rule in app.rules:
            print("Rule", rule.guid,
                  ((" as " + rule.surname) if rule.surname else ""))
            print("  from '" + rule.identifier_as_text + "'")
            print("    to '" + rule.renamer_as_text + "'")
            print("  options:", ("name only"
                                   if rule.only_filename
                                   else "full path"))


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

        for entry in args.entries:
            count = self.apply(app.rules, entry, args.rule)
            logger.info("Found and tested on {} rules".format(count))


    def manual_test(self, args):
        logger.info("action: manual test")

        rules = engine.Rules()
        rule = self._add_rule(rules, args)

        for entry in args.entries:
            count = self.apply(rules, entry)
            logger.info("Tested {} -> {} on {} rules".format(
                rule.identifier_as_text, rule.renamer_as_text, count))


class FolderCommands(Commands):
    def __init__(self, config: conf.Conf):
        self.config = config


    def scan(self, args):
        logger.info("action: scan")

        app = App()
        app.load_rules(args.dbpath)

        total = 0
        files_counter = 0
        for entry in scan_fs(args.paths, max_depth=args.max_depth,
                             recursive=args.recursive):
            count = self.apply(app.rules, entry, args.rule)
            total += count
            if count > 0:
                files_counter += 1

        logger.info("Scan and tested on {} files, with {} renames"
                    .format(files_counter, total))
        if files_counter > 0:
            print("Files: {}".format(files_counter))


class TrainingCommands(Commands):
    def __init__(self, config: conf.Conf):
        self.config = config


    def create(self, args):
        logger.info("training create dataset")

        app = App()
        app.load_training(self.config.trpath)
        for dataset_name in args.names:
            app.training.create(dataset_name)
        app.save_training()


    def list(self, args):
        logger.info("training list of dataset")

        app = App()
        app.load_training(self.config.trpath)

        ds = None
        if args.names:
            ds = filter(lambda x: x != (),
                        (app.training.get(n) for n in args.names))
        else:
            ds = iter(app.training)

        for (name, data) in ds:
            print("Dataset", name)
            for d in data:
                print(" '", d, "'", sep="")


    def insert(self, args):
        logger.info("training insert into dataset")

        app = App()
        app.load_training(self.config.trpath)
        app.training.insert(args.name, args.entries, args.creation)
        app.save_training()


    def drop(self, args):
        logger.info("training remove dataset")

        app = App()
        app.load_training(self.config.trpath)
        for dataset_name in args.names:
            app.training.drop(dataset_name)
        app.save_training()


class Args:
    def __init__(self):
        self.config = None


    def main(self):
        parser = argparse.ArgumentParser(
            description="File identification and rename action."
        )
        self._add_conf(parser, depth=1)
        subparser = parser.add_subparsers(
            title="mode",
            dest="mode",
            help="Mode to use")
        self.install_scan_path(subparser)
        self.install_test_rules(subparser)
        self.install_manual_test(subparser)
        train_parser = self.install_training(subparser)
        rule_parser = self.install_rules(subparser)

        args = parser.parse_args()
        self.resolve(args,
                     parser.print_help,
                     rule_parser.print_help,
                     train_parser.print_help)


    def resolve(self, args,
                mode_help,
                rule_help,
                train_help):

        self._found_conf(args)
        if args.cfpath:
            self.config = conf.load_conf(args.cfpath)
        else:
            self.config = conf.default_conf()

        rc = RuleCommands(self.config)
        fc = FolderCommands(self.config)
        tc = TrainingCommands(self.config)

        action = {
            "_key": "mode",
            "_help": mode_help,
            "scan": fc.scan,
            "test": rc.test,
            "manual-test": rc.manual_test,
            "rules": {
                "_key": "action",
                "_help": rule_help,
                "add": rc.add,
                "list": rc.list,
                "remove": rc.remove
            },
            "train": {
                "_key": "action",
                "_help": train_help,
                "create": tc.create,
                "list": tc.list,
                "insert": tc.insert,
                "drop": tc.drop
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


    def _add_conf(self, parser, depth: int):
        """
        Insert the configuration file parse option into the give parser.
        """
        parser.add_argument("-f", "--config",
                            help="configuration file",
                            metavar="path",
                            dest="cfpath" + str(depth))


    def _found_conf(self, args):
        """
        Find the first `cfpathX` and store it in `cfpath`.
        """
        path = None
        depth = 1
        key = "cfpath" + str(depth)
        while path is None and hasattr(args, key):
            path = getattr(args, key)
            depth += 1
            key = "cfpath" + str(depth)
        args.cfpath = path


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
        self._add_conf(parser, depth=2)
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
        self._add_conf(parser, depth=2)
        self._add_db(parser, depth=1)
        parser.add_argument("--rule",
                            help="id or surname of a rule",
                            metavar="r")
        parser.add_argument("entries",
                            help="entry to test",
                            metavar="entry",
                            nargs="+")
        return parser


    def install_manual_test(self, subparser):
        parser = subparser.add_parser(
            "manual-test",
            help="Manual test with rule specification."
        )
        parser.add_argument("id_rule",
                            help="regular expression to identify filename")
        parser.add_argument("rename_rule",
                            help="format rule to rename filename")
        parser.add_argument("entries",
                            help="entry to test",
                            metavar="entry",
                            nargs="*")
        return parser


    def install_rules(self, subparser):
        parser = subparser.add_parser(
            "rules",
            help="Manage rules."
        )
        self._add_conf(parser, depth=2)
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
        self._add_conf(parser, depth=3)
        self._add_db(parser, depth=2)
        parser.add_argument("id_rule",
                            help="regular expression to identify filename")
        parser.add_argument("rename_rule",
                            help="format rule to rename filename")
        parser.add_argument("surname",
                            nargs="?",
                            help="surname of the rule")
        parser.add_argument("--fullpath",
                            help=("match full path of file "
                            "instead of file name only"),
                            action="store_true")
        return parser


    def install_list_rules(self, subparser):
        parser = subparser.add_parser(
            "list",
            help="List rules."
        )
        self._add_conf(parser, depth=3)
        self._add_db(parser, depth=2)
        return parser


    def install_remove_rule(self, subparser):
        parser = subparser.add_parser(
            "remove",
            help="Remove a rule."
        )
        self._add_conf(parser, depth=3)
        self._add_db(parser, depth=2)
        parser.add_argument("rule_id",
                            help="unique id of the rule")
        return parser


    def install_training(self, subparser):
        parser = subparser.add_parser(
            "train",
            help="Manage training dataset."
        )
        self._add_conf(parser, depth=2)

        subsubparser = parser.add_subparsers(
            title="action",
            dest="action",
            help="Action to do")
        self.install_create_training_dataset(subsubparser)
        self.install_list_training_dataset(subsubparser)
        self.install_insert_into_training_dataset(subsubparser)
        self.install_drop_training_dataset(subsubparser)
        return parser


    def install_create_training_dataset(self, subparser):
        parser = subparser.add_parser(
            "create",
            help="Create a training dataset."
        )
        self._add_conf(parser, depth=3)
        parser.add_argument("names",
                            help="training dataset name",
                            metavar="name",
                            nargs="+")
        return parser


    def install_list_training_dataset(self, subparser):
        parser = subparser.add_parser(
            "list",
            help="List training datasets."
        )
        self._add_conf(parser, depth=3)
        parser.add_argument("names",
                            help="training dataset name to select",
                            metavar="name",
                            nargs="*")
        return parser


    def install_insert_into_training_dataset(self, subparser):
        parser = subparser.add_parser(
            "insert",
            help="Insert data into training dataset."
        )
        self._add_conf(parser, depth=3)
        parser.add_argument("name",
                            help="training dataset name")
        parser.add_argument("entries",
                            help="training entry",
                            nargs="*",
                            metavar="entry")
        parser.add_argument("--create",
                            help="create dataset if doesn't exist",
                            action="store_true",
                            dest="creation")
        return parser


    def install_drop_training_dataset(self, subparser):
        parser = subparser.add_parser(
            "drop",
            help="Drop training datasets."
        )
        self._add_conf(parser, depth=3)
        parser.add_argument("names",
                            help="training dataset name to drop",
                            metavar="name",
                            nargs="*")
        return parser


if __name__ == "__main__":
    ret = Args().main()
    exit(0 if ret is None else ret)
