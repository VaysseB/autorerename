
from pathlib import Path
import datetime
import pickle


MAGIC_NUMBER = 0x1100FE


class ActionFlag(int):
    # Flag part
    RENAMED         = 0b0001
    MANUAL          = 0b0010

    # Flag holder
    SIMULATION      = 0 # not RENAMED
    AUTO_SCAN       = 0 # not MANUAL

    @property
    def was_renamed(self) -> bool:
        return bool(self & self.RENAMED)

    @property
    def is_simulated(self) -> bool:
        return not (self & self.RENAMED)

    @property
    def is_manual(self) -> bool:
        return bool(self & self.MANUAL)

    @property
    def is_auto(self) -> bool:
        return not (self & self.MANUAL)

    is_scan = is_auto

    @staticmethod
    def from_(manual:bool, simulation:bool):
        res = 0
        if not simulation:
            res += ActionFlag.RENAMED
        if manual:
            res += ActionFlag.MANUAL
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

    def start_write(self):
        self._file = open(str(self.log_path), "a+b")
        self._picklog = pickle.Pickler(self._file)

    def end(self):
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
