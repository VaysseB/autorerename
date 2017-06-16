
from pathlib import Path
import pickle


MAGIC_NUMBER = 0x1100FE


class Renamer:
    """
    Class to rename/move files.
    All actions are logged into a file prior and after execution.
    """

    def __init__(self, path: str=None):
        self.log_path = path
        self._file = None
        self._log = None

    def start(self):
        self._file = open(self.log_path, "a+b")
        self._log = pickle.Pickler(self._file)

    def end(self):
        self._log = None
        self._file.flush()
        self._file.close()
        self._file = None

    def _log_before(self, from_: Path, to: Path):
        self._log.dump(MAGIC_NUMBER)
        self._log.dump(str(from_))
        self._log.dump(str(to))

    def _log_after(self, success: bool):
        self._log.dump(success)
        self._file.flush()

    @property
    def rename_log_ready(self):
        return self._log is not None

    def rename(self, from_: Path, to: Path) -> bool:
        assert self.rename_log_ready
        self._log_before(from_, to)
        try:
            from_.rename(to)
            result = True
        except FileNotFoundError:
            result = False
        self._log_after(result)
        return result
