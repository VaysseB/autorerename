
from pathlib import Path
import datetime
import pickle


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


class Renamer:
    """
    Class to rename/move files.
    All actions are logged into a file prior and after execution.
    """

    def __init__(self, path: str=None):
        self.log_path = path
        self._file = None
        self._picklog = None
        self.is_silent_simulation = False

    def start_write(self, is_silent_simulation: bool=False):
        self.is_silent_simulation = is_silent_simulation
        if is_silent_simulation:
            return

        self._file = open(str(self.log_path), "a+b")
        self._picklog = pickle.Pickler(self._file)

    def end(self):
        if self.is_silent_simulation:
            return

        self._picklog = None
        self._file.flush()
        self._file.close()
        self._file = None

    def _dump_log_before(self,
                         source: Path,
                         dest: Path,
                         when: datetime.datetime,
                         rule_id: str,
                         mode: ActionFlag):
        # MAGIC_NUMBER will works as a separator to virtual ends the
        # previous/last action
        self._picklog.dump(MAGIC_NUMBER)

        # general info about the action
        self._picklog.dump(str(when.isoformat()))
        self._picklog.dump(str(rule_id))
        self._picklog.dump(int(mode))

        # files to rename, as in absolute (their real path) and
        # as they were seen
        self._picklog.dump(str(source.absolute()))
        self._picklog.dump(str(dest.absolute()))
        self._picklog.dump(str(source))
        self._picklog.dump(str(dest))

    def _dump_log_after(self, success: bool):
        self._picklog.dump(success)
        self._file.flush()

    @property
    def rename_dump_log_ready(self):
        return self._picklog is not None

    def rename(self,
               source: Path,
               dest: Path,
               rule_id: str,
               action_mode: ActionFlag) -> bool:
        if self.is_silent_simulation:
            return True

        assert self.rename_dump_log_ready
        self._dump_log_before(source, dest,
                              datetime.datetime.now(),
                              rule_id,
                              action_mode)

        try:
            if action_mode.was_renamed:
                source.rename(dest)
            result = True
        except FileNotFoundError:
            result = False

        self._dump_log_after(result)

        return result

    def start_read(self):
        try:
            self._file = open(str(self.log_path), "rb")
        except FileNotFoundError:
            import io
            self._file = io.BytesIO()
        finally:
            self._picklog = pickle.Unpickler(self._file)

    def logs(self):
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


def clear_log(log_path: Path) -> bool:
    if not log_path.exists():
        return True
    elif log_path.is_file():
        log_path.unlink()
    return not log_path.exists()
