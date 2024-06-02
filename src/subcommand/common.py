import codecs
from typing import Callable, Any
from os.path import exists

from cli import ARG_ENABLE, ARG_MULTIPLE, MutuallyExclusiveGroup, Parameter, ParameterGroup
from filerange import FileRange, filerange
from logger import LogFormatter, error, info, warn
from srt import SRTFile
from subtitles import SubtitleLine
import stime
import term

def in_linerange(linerange: tuple[int, int]) -> Callable[[SubtitleLine], bool]:
    '''Yield filter function for linerange'''
    start, end = linerange
    if start == 0 and end == -1:
        return lambda _: True
    elif end == -1:
        return lambda line: start <= line.index
    else:
        return lambda line: start <= line.index and line.index < end

def in_timerange(timerange: stime.TimeRange) -> Callable[[SubtitleLine], bool]:
    '''Yield filter function for linerange'''
    if timerange.end.value == -1:
        return lambda line: timerange.begin.value <= line.duration.begin.value
    else:
        return lambda line: timerange.time_in_range(line.duration.begin)

def filerange_filter_function(filerange: FileRange) \
        -> Callable[[SubtitleLine], bool]:
    '''Yield filter function specified for filerange'''
    if filerange.linerange is not None:
        return in_linerange(filerange.linerange)

    elif filerange.timerange is not None:
        return in_timerange(filerange.timerange)

    else:
        return lambda _: True

def save_subtitle_file(file: SRTFile, args: dict[str, Any]) -> None:
    '''Save subtitle file to specified filename'''
    filename: str
    if args["overwrite"]:
        filename = file.filerange.filename
    else:
        filename = args["output"]

    write_success: bool
    if args["overwrite"]:
        info(f"Overwriting '{filename}' with {len(file.sublines)} lines")
        write_success = file.save_to_file()

    elif exists(filename):
        # TODO add confirm flag
        # TODO change to use terminal prompting (UPCOMING)
        info(f"File '{filename}' already exists")
        if input("Are you sure you want to overwrite it? (Y/n) ") != "Y":
            write_success = False

        else:
            info(f"Writing {len(file.sublines)} lines to existing file"\
                    " '{filename}'")
            write_success = file.write_to_file(filename)

    else:
        info(f"Writing {len(file.sublines)} lines to new file '{filename}'")
        write_success = file.write_to_file(filename)

    use_term_colors: bool = False
    log_formatter: LogFormatter | None = args.get("log_formatter")
    if log_formatter is not None:
        use_term_colors = log_formatter.flags.use_term_colors

    if write_success and use_term_colors:
        prefix = term.term_color_fg("green")
        postfix = term.term_color_fg("default")
        info(f"{prefix}Finished!{postfix}")

    elif write_success:
        info("Finished!")

    else:
        error(f"Fatal error: could not save file '{filename}'")

def validate_input_filetype(args: dict[str, Any]) -> bool:
    '''Validate `args.input`; return false to stop execution'''
    filename: str = args["input"].filename
    if not filename.endswith(".srt"):
        error(f"'{filename}' is not an srt file")
        if ':' in filename:
            warn("If you specified a range, see --use-ranges for help")
        return False

    return True

def validate_many_input_filetypes(args: dict[str, Any]) -> bool:
    '''Validate srt filetypes in `args.input`; false if invalid'''
    for filerange_ in args["input"]:
        if not filerange_.filename.endswith(".srt"):
            error(f"'{filerange_.filename} is not an srt file")
            if ':' in filerange_.filename:
                warn("If you specified a range, use -R to enable" \
                        " range parsing")
            return False

    return True

def validate_encoding(args: dict[str, Any]) -> bool:
    '''Validate encoding is a known value'''
    encoding = args["encoding"]
    try:
        codecs.lookup(encoding)
    except LookupError:
        error(f"'{encoding}' is not a known encoding")
        return False

    return True

def parse_promised_filerange(args: dict[str, Any]) -> None:
    '''Parse file input to FileRange depending on conditions'''
    if args["use_ranges"]:
        args["input"] = filerange(args["input"])

    else:
        args["input"] = FileRange(args["input"], None, None)

def parse_many_promised_fileranges(args: dict[str, Any]) -> None:
    '''Parse file input to FileRange conditionally for many inputs'''
    parse_fn: Callable[[str], FileRange]
    if args["use_ranges"]:
        parse_fn = lambda input_: filerange(input_)

    else:
        parse_fn = lambda input_: FileRange(input_, None, None)

    args["input"] = [parse_fn(value) for value in args["input"]]

def single_srt_file_input_params() -> ParameterGroup:
    '''Return options to implement SRT file input for a command'''
    return ParameterGroup(
            parameters = [
                Parameter(
                    name = "input",
                    helpstring = "The input file"),
                Parameter(
                    name = "--use_ranges",
                    helpstring = "Enable parsing for ranges of lines or"\
                            " timestamps",
                    type = ARG_ENABLE),
                Parameter(
                    name = "--encoding",
                    helpstring = "The encoding for the input file",
                    display_name = "encoding",
                    default = "utf-8")
                ],
            deferred_validators = [
                validate_input_filetype,
                validate_encoding
                ],
            deferred_post_processers = [parse_promised_filerange])

def multiple_srt_file_input_params() -> ParameterGroup:
    '''Return options to implement many SRT file input for a command'''
    return ParameterGroup(
            parameters = [
                Parameter(
                    name = "input",
                    helpstring = "Input files for command",
                    type = ARG_MULTIPLE),
                Parameter(
                    name = "--use-ranges",
                    helpstring = "Enable parsing for ranges of lines or"\
                            " timestamps",
                    type = ARG_ENABLE),
                Parameter(
                    name = "--encoding",
                    helpstring = "The encoding for the input files",
                    display_name = "encoding",
                    default = "utf-8")
                ],
            deferred_validators = [
                validate_many_input_filetypes,
                validate_encoding
                ],
            deferred_post_processers = [parse_many_promised_fileranges])

def srt_file_output_params() -> MutuallyExclusiveGroup:
    '''Return options to implement file output for a command'''
    return MutuallyExclusiveGroup(
            parameters = [
                Parameter(
                    name = "-o",
                    helpstring = "The output file",
                    long_name = "--output",
                    display_name = "output_file"),
                Parameter(
                    name = "-O",
                    helpstring = "Overwrite input file",
                    long_name = "--overwrite",
                    type = ARG_ENABLE)
                ],
            required = True)

