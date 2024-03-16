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
        lines: list[str] = []
        for line in file:
            line = line.strip('\n')
            if len(line) > 0:
                lines.append(line)
                continue

            sublines.append(SubtitleLine.parse(lines))
            lines = []

        if len(lines) > 0:
            sublines.append(SubtitleLine.parse(lines))

    return result
