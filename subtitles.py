from typing import TypeVar, Type
from dataclasses import dataclass

HOURS = 1000 * 60 * 60
MINUTES = 1000 * 60
SECONDS = 1000

T = TypeVar('T', bound = 'Parent')

@dataclass
class Time:
    value: int

    def __str__(self) -> str:
        hour, minute, second, millisecond = self.convertValueToTime(self.value)
        return f"{hour:02}:{minute:02}:{second:02},{millisecond:03}"

    @classmethod
    def fromStr(cls: Type[T], time: str) -> T:
        '''Parse time from string'''

        hourStr, minuteStr, remainder = time.split(':')
        secondStr, millisecondStr = remainder.split(',')
        hour = int(hourStr)
        minute = int(minuteStr)
        second = int(secondStr)
        millisecond = int(millisecondStr)
        return cls(cls.convertTimeToValue(hour, minute, second, millisecond))

    @staticmethod
    def convertTimeToValue(
            hour: int,
            minute: int,
            second: int,
            millisecond: int) -> int:
        '''Converts from seperated time to internal value'''

        return (millisecond + second*SECONDS + minute*MINUTES + hour*HOURS)

    @staticmethod
    def convertValueToTime(value: int) -> tuple[int, int, int, int]:
        '''Convert from internal value to seperated time'''

        hour, value = divmod(value, HOURS)
        minute, value = divmod(value, MINUTES)
        second, millisecond = divmod(value, SECONDS)
        return (hour, minute, second, millisecond)

@dataclass
class TimeRange:
    begin: Time
    end: Time

    def addDelay(self, milliseconds: int) -> None:
        '''Add delay to both endpoints of duration'''

        self.begin.value = self.begin.value + milliseconds
        self.end.value = self.end.value + milliseconds

    def __str__(self) -> str:
        return f"{self.begin!s} --> {self.end!s}"

    @classmethod
    def parseDuration(cls: Type[T], duration: str) -> T:
        '''Parses duration line from srt file'''

        beginStr, endStr = duration.split(" --> ")
        return cls(Time.fromStr(beginStr), Time.fromStr(endStr))

@dataclass
class SubtitleLine:
    duration: TimeRange
    content: list[str]

    @classmethod
    def parse(cls: Type[T], lines: list[str]) -> T:
        '''Parse a sequences of non-empty lines into subtitle lines'''

        # ignore index line
        durationStr = lines[1]
        content = lines[2:]
        duration = TimeRange.parseDuration(durationStr)
        return cls(duration, content)
