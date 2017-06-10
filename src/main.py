
import argparse

import logger
import engine
import well


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


    def main(self):
        modes = {
            "rule": self.rules
        }

        parser = argparse.ArgumentParser(
            description="TODO",
            prog=self.prog_name
        )
        parser.add_argument("mode", choices=modes.keys(),
                            help="Mode to use")
        args = parser.parse_args(self.args[0:1])

        self.prog_name += " " + args.mode
        modes[args.mode]()


    def rules(self):
        actions = {
            "add": self.rules_add
        }

        parser = argparse.ArgumentParser(
            description="Manage rules",
            prog=self.prog_name
        )
        parser.add_argument("action", choices=actions.keys())
        args = parser.parse_args(self.args[1:2])

        self.prog_name += " " + args.action
        actions[args.action]()


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
        args = parser.parse_args(self.args[2:])

        logger.info("cmd args: %s", " ".join(self.args))
        logger.info("action: add a rule")
        self.app.load_rules(args.database)
        self.app.rules.add(args.id_rule, args.rename_rule)
        self.app.save_rules()


if __name__ == "__main__":
    Args().main()
