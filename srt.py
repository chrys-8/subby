from enum import Enum
from typing import Any, Callable
from dataclasses import dataclass

from subtitles import SubtitleLine, TimeRange, Time

@dataclass
class SubtitleFile:
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

class ParserState(Enum):
    BeforeSubline = 0
    FirstLine = 1
    IndexLine = 2
    DurationLine = 3
    Contents = 4
    EndOfSubline = 5

def decodeSRTFile(filename: str) -> SubtitleFile | None:
    '''Decode srt file'''

    try:
        file = open(filename, 'r')
    except FileNotFoundError:
        print("File not found error")
        return

    sublines: list[SubtitleLine] = list()
    result: SubtitleFile = SubtitleFile(filename, sublines)

    with file:
        # abstract with builder pattern
        index: int = 0
        duration: TimeRange = TimeRange(Time(0), Time(0))
        content: list[str] = list()
        state = ParserState.FirstLine

        for line in file:
            line = line.strip('\n')

            if state is ParserState.FirstLine:
                line = removeByteOrderMark(line)
                state = ParserState.BeforeSubline

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

    return result
