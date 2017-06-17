
import sys
import argparse
from pathlib import Path

import logger
import engine
import well
import conf
import action
from utils import *


EXIT_ERROR = 1


class App:
    """
    Bundle of resources to of the application.
    """

    def __init__(self):
        self.rules = None
        self.rule_path = None
        self.renamer = None

    def phony_rules(self):
        self.rules = engine.Rules()

    def load_rules(self, filepath: Path):
        self.rule_path = filepath
        self.rules = well.load_rules(filepath)

    def save_rules(self):
        if self.rule_path:
            well.save_rules(self.rule_path, self.rules)
        else:
            logger.warn("no path of database to save rules")

    def open_action_log(self, logpath: Path):
        self.renamer = action.Renamer(str(logpath.resolve()))
        self.renamer.start_read()

    def start_action(self, logpath: Path):
        self.renamer = action.Renamer(str(logpath.resolve()))
        self.renamer.start_write()
        self.rename = self.renamer.rename

    def end_action(self):
        self.rename = None
        self.renamer.end()
        self.renamer = None


class Commands:
    """
    Common functions to all commands.
    """

    def _reformat(self,
                  rules: engine.Rules,
                  entry: Path,
                  rule_id_or_name: str=None) -> int:
        for (rule, entry, match) in rules.find_applying(entry, rule_id_or_name):
            result = rule.format(entry, match)
            yield (rule, result)

    def _add_rule(self, rules: engine.Rules, args):
        """
        Add a rule from data in args.
        Shorthand version.
        """
        rule = rules.add(
            id_rule=args.id_rule,
            rename_rule=args.rename_rule,
            name=getattr(args, "name", None))
        return rule


class RuleCommands(Commands):
    """
    Commands CRUD on rules and test.
    """

    def __init__(self, config: conf.Conf):
        self.config = config

    def add(self, args):
        """
        Add a rule in the database.
        """
        logger.info("action: add a rule")

        app = App()
        app.load_rules(args.dbpath)
        self._add_rule(app.rules, args)
        app.save_rules()

    def list(self, args):
        """
        List rules from the database.
        """
        logger.info("action: list rules")

        app = App()
        app.load_rules(args.dbpath)

        for rule in app.rules:
            print("Rule", rule.guid,
                  ((" as " + rule.name) if rule.name else ""))
            print("  from '" + rule.identifier_as_text + "'")
            print("    to '" + rule.renamer_as_text + "'")

    def remove(self, args):
        """
        Remove a rule from the database.
        """
        logger.info("action: remove rule(s)")

        app = App()
        app.load_rules(args.dbpath)

        success = True
        for rule_lkup in args.rules_lkup:
            success &= app.rules.remove(guid=rule_lkup, name=rule_lkup)
        app.save_rules()

        if not success:
            return EXIT_ERROR


class FileCommands(Commands):
    """
    Commands applying on path.
    """

    def __init__(self, config: conf.Conf):
        self.config = config
        self.app = App()

    def test(self, args):
        """
        Find known rules applying from handmade entries and simulate the output.
        """
        logger.info("action: test")

        self.app.load_rules(args.dbpath)
        self.app.start_action(self.config.actlog_path)
        # TODO add a cmd switch to disable automatic log (and in conf)

        for entry in (Path(p) for p in args.entries):
            self._apply(entry, args.rule_lkup,
                        user_given_entry=True,
                        rule_is_manual=False,
                        simulation=True)

        dir_paths = (Path(p) for p in args.dir_paths)
        for entry in scan_fs(dir_paths, recursive=False):
            self._apply(entry, args.rule_lkup,
                        user_given_entry=False,
                        rule_is_manual=False,
                        simulation=True)

        recur_paths = (Path(p) for p in args.recur_paths)
        for entry in scan_fs(recur_paths, recursive=True):
            self._apply(entry, args.rule_lkup,
                        user_given_entry=False,
                        rule_is_manual=False,
                        simulation=True)

        self.app.end_action()

    def rename(self, args):
        """
        Apply first found rules applying from handmade entries and simulate the output.
        """
        logger.info("action: execution")

        self.app.load_rules(args.dbpath)
        self.app.start_action(self.config.actlog_path)

        for entry in (Path(p) for p in args.entries):
            self._apply(entry, args.rule_lkup,
                        user_given_entry=True,
                        rule_is_manual=False,
                        simulation=False)

        self.app.end_action()

    def _status(self,
                success: bool,
                action_mode: action.Flag):
        status = ""
        if not success:
            status = "!"
        else:
            status = ("S"
                      if action_mode.is_simulated
                      else "#")

        status += ("m"
                   if action_mode.rule_is_manual
                   else "r")
        status += ("s"
                   if action_mode.entry_was_found
                   else "i")

        return status

    def _apply(self,
               entry: Path,
               rule_id_or_name: str,
               **kw):
        action_mode = action.Flag.from_(**kw)

        for (rule, new_entry) in self._reformat(self.app.rules, entry, rule_id_or_name):

            # actually rename (if not a simulation) the file
            success = self.app.rename(entry, new_entry, rule.guid, action_mode)

            # log to the user what has been done
            print("{}:{}: '{}' --> '{}'".format(
                self._status(success, action_mode),
                rule.name_prefix(), entry, new_entry))

            if not success:
                print("Failed to rename '{}' to '{}'".format(entry, new_entry),
                      file=sys.stderr)

            # stop trying to rename the file if it succeed and as it is for real
            if action_mode.was_renamed and success:
                break

    def log(self, args):
        """
        Dump the action log.
        """
        logger.info("action: log")

        app = App()
        app.open_action_log(self.config.actlog_path)

        # TODO add format input from cmd
        for line in app.renamer.logs():
            s = self._status(line.success, line.mode)
            print("{}: '{}' --> '{}'".format(s, line.source, line.dest))

    def manual_test(self, args):
        """
        Create a temporary rule and try handmade entries on it.
        """
        logger.info("action: manual test")

        self.app.phony_rules()
        rule = self._add_rule(self.app.rules, args)

        self.app.start_action(self.config.actlog_path)
        # TODO add a cmd switch to disable automatic log (and in conf)

        for entry in (Path(p) for p in args.entries):
            self._apply(entry, rule.guid,
                        user_given_entry=True,
                        rule_is_manual=True,
                        simulation=True)

        self.app.end_action()


class Args:
    """
    Command line argument parser and action performer.
    """

    def main(self):
        """
        Entry point to parse command lines arguments, and
        dispatch to the right action.
        """

        # build command line argument parser
        parser = argparse.ArgumentParser(
            description="File identification and rename action."
        )
        self._add_conf_argument(parser, depth=1)
        subparser = parser.add_subparsers(
            title="mode",
            dest="mode",
            help="Mode to use")
        self.install_action(subparser)
        self.install_log(subparser)
        self.install_test(subparser)
        self.install_manual_test(subparser)
        rule_parser = self.install_rules(subparser)

        # identify what action to do and execute it
        args = parser.parse_args()
        self.load_conf(args)
        self.find_dbpath(args)
        self.resolve(args,
                     parser.print_help,
                     rule_parser.print_help)

    def load_conf(self, args):
        """
        Load the configuration file from standard paths or in arguments.
        """
        self._collapse_arg(args, "cfpath")
        if args.cfpath:
            self.config = conf.load_conf(Path(args.cfpath).resolve())
        else:
            self.config = conf.default_conf()

    def find_dbpath(self, args):
        """
        Find database path from configuration file or cmd line argument.
        """
        self._collapse_arg(args, "dbpath")
        if args.dbpath is None:
            args.dbpath = self.config.dbpath
        args.dbpath = Path(args.dbpath)

    def resolve(self, args,
                mode_help,
                rule_help):
        """
        Find what action to and execute it.
        """
        # specify all commands possible
        rc = RuleCommands(self.config)
        fc = FileCommands(self.config)

        # actions reachable from cmd line args
        # special "_key" : key to find the value in args to find the next action
        # special "_help": help to use in case of unknown value
        action = {
            "_key": "mode",
            "_help": mode_help,
            "test": fc.test,
            "log": fc.log,
            "rename": fc.rename,
            "manual-test": fc.manual_test,
            "rules": {
                "_key": "action",
                "_help": rule_help,
                "add": rc.add,
                "list": rc.list,
                "remove": rc.remove
            },
        }

        # resolve command to apply
        while not callable(action) and action is not None:
            key = action["_key"]
            help = lambda _, f=action["_help"]: f()
            next = getattr(args, key)
            action = action.get(next, help)

        # do action
        action(args)

    def _add_conf_argument(self, parser, depth: int):
        """
        Insert the configuration file parse option into the give parser.
        """
        parser.add_argument("-f", "--file",
                            help="configuration file",
                            metavar="path",
                            dest="cfpath" + str(depth))

    def _add_db_argument(self, parser, depth: int):
        """
        Insert the database parse option into the give parser.
        """
        parser.add_argument("--database",
                            help="database of rules",
                            metavar="path",
                            dest="dbpath" + str(depth))

    def _insert_rule_lookup(self, parser,
                            optional: bool=True,
                            multiple: bool=False):
        if optional:
            return parser.add_argument(
                "--rule",
                help="id or name of a rule",
                metavar="r",
                dest="rule_lkup",
                action=("append" if multiple else "store"))
        else:
            return parser.add_argument(
                "rules_lkup",
                help="id or name of a rule",
                metavar="rule",
                nargs=("+" if multiple else 1),
                action=("append" if multiple else "store"))

    def _collapse_arg(self, args, prefix: str):
        """
        Find in args the first "<prefix><number>" and save into <prefix> the
        first found.
        """
        value = None
        depth = 1
        key = prefix + str(depth)
        while value is None and hasattr(args, key):
            value = getattr(args, key)
            depth += 1
            key = prefix + str(depth)
        setattr(args, prefix, value)

    def install_action(self, subparser):
        parser = subparser.add_parser(
            "rename",
            help="Rename files."
        )
        self._add_conf_argument(parser, depth=2)
        self._add_db_argument(parser, depth=1)
        self._insert_rule_lookup(parser)
        parser.add_argument("entries",
                            help="manual entries to rename",
                            metavar="text",
                            nargs="*",
                            default=[])
        return parser

    def install_log(self, subparser):
        parser = subparser.add_parser(
            "log",
            help="Print the rename log."
        )
        self._add_conf_argument(parser, depth=2)
        return parser

    def install_test(self, subparser):
        parser = subparser.add_parser(
            "test",
            help="Testing of rules and their application."
        )
        self._add_conf_argument(parser, depth=2)
        self._add_db_argument(parser, depth=1)
        self._insert_rule_lookup(parser)
        parser.add_argument("entries",
                            help="manual entries to test",
                            metavar="text",
                            nargs="*",
                            default=[])
        parser.add_argument("-s", "--scan",
                            help="test on files from given path, not recursive",
                            metavar="path",
                            action="append",
                            dest="dir_paths",
                            default=[])
        parser.add_argument("-r", "--recursive",
                            help="test on files from given path, recursive",
                            metavar="path",
                            action="append",
                            dest="recur_paths",
                            default=[])
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
        self._add_conf_argument(parser, depth=2)
        self._add_db_argument(parser, depth=1)

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
        self._add_conf_argument(parser, depth=3)
        self._add_db_argument(parser, depth=2)
        parser.add_argument("id_rule",
                            help="regular expression to identify filename")
        parser.add_argument("rename_rule",
                            help="format rule to rename filename")
        parser.add_argument("name",
                            help="name of the rule (optional)",
                            nargs="?")
        return parser

    def install_list_rules(self, subparser):
        parser = subparser.add_parser(
            "list",
            help="List rules."
        )
        self._add_conf_argument(parser, depth=3)
        self._add_db_argument(parser, depth=2)
        return parser

    def install_remove_rule(self, subparser):
        parser = subparser.add_parser(
            "remove",
            help="Remove a rule."
        )
        self._add_conf_argument(parser, depth=3)
        self._add_db_argument(parser, depth=2)
        self._insert_rule_lookup(parser, optional=False)
        return parser


if __name__ == "__main__":
    ret = Args().main()
    exit(0 if ret is None else ret)
