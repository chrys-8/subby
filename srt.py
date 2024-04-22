from enum import Enum, auto
from typing import Any, Callable
from dataclasses import dataclass

from subtitles import SubtitleLine
from stime import TimeRange, Time
from filerange import FileRange

@dataclass
class FileStatistics:
    consecutive_blank_lines: tuple[int, ...] = ()
    missing_end_blank_line: bool = False

@dataclass
class SRTFile:
    filerange: FileRange
    sublines: list[SubtitleLine]
    encoding: str

    def print(self) -> None:
        '''Output to stdout'''

        def _print(s: str) -> None:
            print(s, end='')

        self._output(_print)

    def write_to_file(self, outputFilename: str) -> bool:
        '''Output to file'''

        try:
            file = open(outputFilename, 'w', encoding = self.encoding)
        except OSError:
            return False

        with file:
            self._output(file.write)

        return True

    def save_to_file(self) -> bool:
        '''Save to the source file'''
        return self.write_to_file(self.filerange.filename)

    def _output(self, fn: Callable[[str], Any]) -> None:
        '''Make successive calls to an output function with file contents'''

        for subtitle in self.sublines:
            fn(f"{subtitle.index}\n")
            fn(f"{str(subtitle.duration)}\n")
            for line in subtitle.content:
                fn(f"{line}\n")

            fn("\n")

    def sort_subtitles(self) -> None:
        '''Sort subtitles by ascending start time'''
        self.sublines.sort(key = lambda line: line.duration.begin.value)

def remove_byte_order_mark(line: str) -> str:
    '''Remove BOM at beginning of file'''
    if line.startswith("\xEF\xBB\xBF"):
        line = line[3:]
    return line

class DecodeException(Exception):
    pass

class ParserState(Enum):
    BeforeSubline = auto()
    IndexLine     = auto()
    DurationLine  = auto()
    Contents      = auto()
    EndOfSubline  = auto()

class SRTDecoder:
    '''Implement srt decoding'''
    def __init__(self, filerange: FileRange, encoding: str = "utf-8") -> None:
        self.filerange = filerange
        self.encoding = encoding

        self.filebuffer: list[str] = []
        self.stats = FileStatistics(())

    def set_encoding(self, encoding: str) -> None:
        '''Set file encoding'''
        self.encoding = encoding

    def read_file(self) -> None:
        '''Open file and read to buffer'''
        try:
            with open(self.filerange.filename, 'r', \
                    encoding = self.encoding) as file:
                for line in file:
                    line = line.strip('\n')
                    self.filebuffer.append(line)

        except FileNotFoundError:
            print(f"{self.filerange.filename} cannot be opened")
            raise DecodeException

        except UnicodeDecodeError as err:
            print(f"Unicode encoding error encountered in" \
                    " {self.filerange.filename}:")
            print(err)
            raise DecodeException

        # remove BOM from first line
        self.filebuffer[0] = remove_byte_order_mark(self.filebuffer[0])

    def cleanup(self) -> None:
        '''Free filebuffer'''
        self.filebuffer.clear()

    def decode(self) -> SRTFile:
        '''Run decode implementation'''
        # check if we need to read the file
        if len(self.filebuffer) == 0:
            self.read_file()

        sublines: list[SubtitleLine] = []

        index = 0
        duration = TimeRange(Time(0), Time(0))
        content: list[str] = []
        state = ParserState.BeforeSubline

        consecutive_blank_lines: list[int] = []
        consecutive_blank_line_count = 0

        for line_index, line in enumerate(self.filebuffer):
            if len(line) == 0:
                consecutive_blank_line_count = consecutive_blank_line_count + 1

            else:
                consecutive_blank_line_count = 0

            if consecutive_blank_line_count > 1:
                consecutive_blank_lines.append(line_index)

            if state is ParserState.BeforeSubline:
                try:
                    index = int(line)
                    state = ParserState.DurationLine
                    continue

                except ValueError:
                    pass

            if state is ParserState.DurationLine:
                duration = TimeRange.parse_duration(line)
                state = ParserState.Contents
                continue

            if state is ParserState.Contents:
                if len(line) != 0:
                    content.append(line)
                    continue

                state = ParserState.EndOfSubline

            if state is ParserState.EndOfSubline:
                sublines.append(SubtitleLine(index, duration, content))
                content = []
                state = ParserState.BeforeSubline

        if state is ParserState.Contents:
            # missing blank line at EOF
            sublines.append(SubtitleLine(index, duration, content))
            self.stats.missing_end_blank_line = True

        elif state is not ParserState.BeforeSubline:
            raise DecodeException

        self.cleanup()
        self.stats.consecutive_blank_lines = tuple(consecutive_blank_lines)
        return SRTFile(self.filerange, sublines, self.encoding)

# Structure checks
def check_index_mismatch(file: SRTFile) -> list[tuple[int, int]]:
    '''Discover line index mismatches; yields (reported, actual)'''

    return [(line.index, index)
            for index, line in enumerate(file.sublines)
            if line.index != index + 1]
