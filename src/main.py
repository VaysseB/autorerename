
import argparse

import logger
import engine
import well



class App:

    def __init__(self, name=None, args=None):
        import sys
        self.prog_name = (argparse.ArgumentParser().prog
                          if name is None
                          else name)
        self.args = list((sys.argv[1:] if args is None else args)[:])

    def main(self):
        modes = {
            "rule": self.rules
        }
        origin = self.prog_name

        parser = argparse.ArgumentParser(
            description="TODO",
            prog=self.prog_name
        )
        parser.add_argument("mode", choices=modes.keys(),
                            help="Mode to use")
        args = parser.parse_args(self.args[0:1])

        self.prog_name += " " + args.mode
        modes[args.mode](origin)


    def rules(self, origin: str):
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
        actions[args.action](origin)


    def rules_add(self, origin: str):
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

        print("add a rule", args.id_rule, args.rename_rule, args.database)


if __name__ == "__main__":
    App().main()
