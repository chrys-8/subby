from dataclasses import dataclass

from stime import TimeRange

@dataclass
class SubtitleLine:
    index: int
    duration: TimeRange
    content: list[str]
