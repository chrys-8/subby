from enum import Enum
from typing import Any, Callable
from dataclasses import dataclass

from subtitles import SubtitleLine, TimeRange, Time

@dataclass
class SRTFile:
    filename: str
    sublines: list[SubtitleLine]

    def print(self) -> None:
        '''Output to stdout'''

        def _print(s: str) -> None:
            print(s, end='')

        self._output(_print)

    def writeToFile(self, outputFilename: str) -> bool:
        '''Output to file'''

        try:
            file = open(outputFilename, 'w')
        except OSError:
            return False

        with file:
            self._output(file.write)

        return True

    def saveToFile(self) -> bool:
        '''Save to the source file'''
        return self.writeToFile(self.filename)

    def _output(self, fn: Callable[[str], Any]) -> None:
        '''Make successive calls to an output function with file
        contents'''

        counter = 0
        for subtitle in self.sublines:
            counter = counter + 1
            fn(f"{counter}\n")
            fn(f"{str(subtitle.duration)}\n")
            for line in subtitle.content:
                fn(f"{line}\n")

            fn("\n")

def removeByteOrderMark(line: str) -> str:
    '''Remove BOM at beginning of file'''
    if line.startswith("\xEF\xBB\xBF"):
        line = line[3:]
    return line

class DecodeException(Exception):
    pass

class ParserState(Enum):
    BeforeSubline = 0
    FirstLine = 1
    IndexLine = 2
    DurationLine = 3
    Contents = 4
    EndOfSubline = 5

class SRTDecoder:
    '''Implement srt decoding'''
    def __init__(self, filename: str) -> None:
        self.filename = filename

        self.filebuffer: list[str] = []

    def read_file(self) -> None:
        '''Open file and read to buffer'''
        try:
            file = open(self.filename, 'r')
        except FileNotFoundError:
            print(f"{self.filename} cannot be opened")
            raise DecodeException

        with file:
            for line in file:
                line = line.strip('\n')
                self.filebuffer.append(line)

        # remove BOM from first line
        self.filebuffer[0] = removeByteOrderMark(self.filebuffer[0])

    def cleanup(self) -> None:
        '''Free filebuffer'''
        self.filebuffer.clear()

    def decode(self) -> SRTFile:
        '''Run decode implementation'''
        # check if we need to read the file
        if len(self.filebuffer) == 0:
            self.read_file()

        sublines: list[SubtitleLine] = []

        index: int = 0
        duration: TimeRange = TimeRange(Time(0), Time(0))
        content: list[str] = []
        state = ParserState.BeforeSubline

        for line in self.filebuffer:
            if state is ParserState.BeforeSubline:
                try:
                    index = int(line)
                    state = ParserState.DurationLine
                    continue

                except ValueError:
                    pass

            if state is ParserState.DurationLine:
                duration = TimeRange.parseDuration(line)
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

        self.cleanup()
        return SRTFile(self.filename, sublines)
