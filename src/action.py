
from pathlib import Path
import pickle


MAGIC_NUMBER = 0x1100FE


class LogLine:
    def __init__(self, data):
        self.from_, self.to, *self.other = data

    @property
    def success(self) -> bool:
        if len(self.other) >= 1:
            return self.other[0]


class Renamer:
    """
    Class to rename/move files.
    All actions are logged into a file prior and after execution.
    """

    def __init__(self, path: str=None):
        self.log_path = path
        self._file = None
        self._dump_log = None
        self._read_log = None

    def start_write(self):
        self._file = open(self.log_path, "a+b")
        self._dump_log = pickle.Pickler(self._file)

    def end(self):
        self._dump_log = None
        self._file.flush()
        self._file.close()
        self._file = None

    def _dump_log_before(self, from_: Path, to: Path):
        self._dump_log.dump(MAGIC_NUMBER)
        self._dump_log.dump(str(from_))
        self._dump_log.dump(str(to))

    def _dump_log_after(self, success: bool):
        self._dump_log.dump(success)
        self._file.flush()

    @property
    def rename_dump_log_ready(self):
        return self._dump_log is not None

    def rename(self, from_: Path, to: Path) -> bool:
        assert self.rename_dump_log_ready
        self._dump_log_before(from_, to)
        try:
            from_.rename(to)
            result = True
        except FileNotFoundError:
            result = False
        self._dump_log_after(result)
        return result

    def start_read(self):
        self._file = open(self.log_path, "rb")
        self._read_log = pickle.Unpickler(self._file)

    def logs(self):
        line = []
        try:
            data = self._read_log.load()
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

                data = self._read_log.load()
        except EOFError:
            if line:
                yield LogLine(line)
