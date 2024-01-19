from subtitles import SubtitleLine

@dataclass
class SubtitleFile:
    filename: str
    sublines: list[SubtitleLine]

    def writeToFile(self, outputFilename: str) -> bool:
        '''Output to file'''

        try:
            file = open(outputFilename, 'w')
        except OSError:
            return False

        with file:
            counter = 0
            for subtitle in self.sublines:
                counter = counter + 1
                file.write(f"{counter}\n")
                file.write(f"{str(subtitle.duration)}\n")
                for line in subtitle.content:
                    file.write(f"{line}\n")

                file.write("\n")

        return True

    def saveToFile(self) -> bool:
        '''Save to the source file'''
        return self.writeToFile(self.filename)

def decodeSRTFile(filename: str) -> SubtitleFile | None:
    '''Decode srt file'''

    try:
        file = open(filename, 'r')
    except FileNotFoundError:
        print("File not found error")
        return

    sublines: list[str] = list()
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
