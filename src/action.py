
from pathlib import Path
import datetime
import pickle

import logger


MAGIC_NUMBER = 0x1100FE


class ActionFlag(int):
    # Flag part
    RENAMED         = 0b0001
    MANUAL_RULE     = 0b0010
    USER_ENTRY      = 0b0100

    @property
    def was_renamed(self) -> bool:
        return bool(self & self.RENAMED)

    @property
    def is_simulated(self) -> bool:
        return not (self & self.RENAMED)

    @property
    def rule_is_manual(self) -> bool:
        return bool(self & self.MANUAL_RULE)

    @property
    def registered_rule(self) -> bool:
        return not (self & self.MANUAL_RULE)

    @property
    def entry_was_given_manually(self) -> bool:
        return bool(self & self.USER_ENTRY)

    @property
    def entry_was_found(self) -> bool:
        return not (self & self.USER_ENTRY)

    @staticmethod
    def from_(user_given_entry: bool,
              rule_is_manual: bool,
              simulation:bool):
        res = 0
        if not simulation:
            res += ActionFlag.RENAMED
        if rule_is_manual:
            res += ActionFlag.MANUAL_RULE
        if user_given_entry:
            res += ActionFlag.USER_ENTRY
        return ActionFlag(res)

Flag = ActionFlag


class LogLine:
    """
    Line from the action log.
    """

    def __init__(self, data):
        (self.when,
         self.rule_id,
         self.mode,
         self.abs_source,
         self.abs_dest,
         self.source,
         self.dest,
         *self._result) = data

        self.mode = ActionFlag(self.mode)

    @property
    def success(self) -> bool:
        if self._result:
            return self._result[0]

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.when, 'auto')


class Log:
    """
    Log of all actions taken (even simulated).
    """

    def __init__(self, path: Path):
        self.path = path
        self._file = None
        self._picklog = None

    def open_write(self):
        """
        Open the log to write into it.
        """
        self._file = open(str(self.path), "a+b")
        self._picklog = pickle.Pickler(self._file)

    def close_write(self):
        """
        Flush the log and disable writing.
        """
        self._picklog = None
        self._file.flush()
        self._file.close()
        self._file = None

    @property
    def ready_to_write(self):
        return self._file and isinstance(self._picklog, pickle.Pickler)

    def write(self, what):
        """
        Write something into the log.
        """
        self._picklog.dump(what)

    def flush(self):
        """
        Force flush of the log file.
        """
        self._file.flush()

    def open_read(self):
        """
        Open the log to read from it.
        """
        try:
            self._file = open(str(self.path), "rb")
        except FileNotFoundError:
            import io
            self._file = io.BytesIO()
        finally:
            self._picklog = pickle.Unpickler(self._file)

    def read_iter(self) -> LogLine:
        """
        Read line by line the log.
        """
        line = []
        try:
            data = self._picklog.load()
            assert data == MAGIC_NUMBER, ("expected the magic number at the start"
                                          "of the file")

            while True:
                # look for start of action
                if data == MAGIC_NUMBER:
                    if line:
                        yield LogLine(line)
                        line.clear()
                else:
                    line.append(data)

                data = self._picklog.load()
        except EOFError:
            if line:
                yield LogLine(line)

    def clear(self) -> bool:
        """
        Makes sure the log file is removed.
        """
        if not self.path.exists():
            return True
        elif self.path.is_file():
            self.path.unlink()
        return not self.path.exists()


class Renamer:
    """
    Class to rename/move files.
    All actions are logged into a file prior and after execution.
    """

    def __init__(self, log: Log):
        self.log = log

    def _dump_log_before(self,
                         source: Path,
                         dest: Path,
                         when: datetime.datetime,
                         rule_id: str,
                         mode: ActionFlag):
        # MAGIC_NUMBER will works as a separator to virtual ends the
        # previous/last action
        self.log.write(MAGIC_NUMBER)

        # general info about the action
        self.log.write(str(when.isoformat()))
        self.log.write(str(rule_id))
        self.log.write(int(mode))

        # files to rename, as in absolute (their real path) and
        # as they were seen
        self.log.write(str(source.absolute()))
        self.log.write(str(dest.absolute()))
        self.log.write(str(source))
        self.log.write(str(dest))

    def _dump_log_after(self, success: bool):
        self.log.write(success)
        self.log.flush()

    def rename(self,
               source: Path,
               dest: Path,
               rule_id: str,
               action_mode: ActionFlag) -> bool:
        assert self.log and self.log.ready_to_write
        self._dump_log_before(source, dest,
                              datetime.datetime.now(),
                              rule_id,
                              action_mode)

        try:
            if action_mode.was_renamed:
                if dest.exists():
                    logger.warn("File already exists: {}".format(dest))
                    return False

                # make sure folder exists if it was changed
                dest.parent.mkdir(parents=False, exist_ok=True)
                # move or rename file
                source.rename(dest)

            result = True
        except FileNotFoundError:
            logger.warn("File not found: {}".format(source))
            result = False

        self._dump_log_after(result)

        return result

