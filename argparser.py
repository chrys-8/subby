import argparse
from dataclasses import dataclass
from typing import Any, Callable, Literal

from filerange import FileRange, filerange
from logger import LogFormatter, LogFlags, error, warn, LEVEL_DEBUG

def validate_input_filetype(args: argparse.Namespace) -> bool:
    '''Validate `args.input`; return false to stop execution'''
    filename: str = args.input.filename
    if not filename.endswith(".srt"):
        error(f"'{filename}' is not an srt file\n")
        if ':' in filename:
            warn("If you specified a range, use -R to enable range" \
                    " parsing\n")
        return False

    return True

def validate_many_input_filetypes(args: argparse.Namespace) -> bool:
    '''Validate srt filetypes in `args.input`; false if invalid'''
    for filerange_ in args.input:
        if not filerange_.filename.endswith(".srt"):
            error(f"'{filerange_.filename} is not an srt file\n")
            if ':' in filerange_.filename:
                warn("If you specified a range, use -R to enable" \
                        " range parsing\n")
            return False

    return True

def parse_promised_filerange(args: argparse.Namespace) -> None:
    '''Parse file input to FileRange depending on conditions'''
    if args.use_ranges:
        args.input = filerange(args.input)

    else:
        args.input = FileRange(args.input, None, None)

def parse_many_promised_fileranges(args: argparse.Namespace) -> None:
    '''Parser file input to FileRange conditionally for many inputs'''
    parse_fn: Callable[[str], FileRange]
    if args.use_ranges:
        parse_fn = lambda input_: filerange(input_)

    else:
        parse_fn = lambda input_: FileRange(input_, None, None)

    args.input = [parse_fn(value) for value in args.input]

ValidatorType = Callable[[argparse.Namespace], bool]
ProcessorType = Callable[[argparse.Namespace], None]

ARG_VALUE    = "value"
ARG_ENABLE   = "enable"
ARG_DISABLE  = "disable"
ARG_OPTIONAL = "optional"

@dataclass
class SubcommandArgument:
    '''Schema for representing subcommand arguments'''
    name: str
    helpstring: str
    long_name: str | None = None
    display_name: str | None = None
    type: Literal["value", "enable", "disable", "optional"] = ARG_VALUE
    choices: tuple[str, ...] | None = None
    value_type: Any = str
    default:Any = None

    def params(self) -> tuple[tuple[str,...], dict[str, Any]]:
        '''Yield params for adding to command line parser'''
        options: dict[str, Any] = {} # kwargs for `parser.add_argument`
        names: list[str] = []

        names.append(self.name)
        if self.long_name is not None:
            names.append(self.long_name)

        options["help"] = self.helpstring
        if self.display_name is not None:
            options["metavar"] = self.display_name

        if self.choices is not None:
            options["choices"] = self.choices

        if self.value_type is not str:
            options["type"] = self.value_type

        if self.default is not None:
            options["default"] = self.default

        if self.type == ARG_ENABLE:
            options["action"] = "store_true"

        elif self.type == ARG_DISABLE:
            options["action"] = "store_false"

        elif self.type == ARG_OPTIONAL:
            options["nargs"] = "?"

        return tuple(names), options

SUBCMD_INPUT_SINGLE = "input_single"
SUBCMD_INPUT_MANY   = "input_many"
SUBCMD_OUTPUT       = "output"

@dataclass
class Subcommand:
    '''Schema for representing subcommands'''
    name: str
    helpstring: str
    function: Callable[[argparse.Namespace], None]
    args: list[SubcommandArgument | Literal["input_single", "input_many",\
            "output"]] | None = None
    validators: list[ValidatorType] | None = None
    post_processors: list[ProcessorType] | None = None

class Subparser:
    '''Wrap ArgumentParser with validators and post processors'''

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser
        self._validators: list[ValidatorType] = []
        self._post_processors: list[ProcessorType] = []

    def add_validator(self, validator: ValidatorType) -> None:
        '''Add validator to parser'''
        self._validators.append(validator)

    def add_post_processor(self, post_processor: ProcessorType) -> None:
        '''Add post_processor to parser'''
        self._post_processors.append(post_processor)

    def parse_args(self) -> argparse.Namespace:
        '''Yield arguments from command line parsing'''
        return self.parser.parse_args()

    def run_post_processors(self, args: argparse.Namespace) -> None:
        '''Perform post processing on arguments'''
        for post_processor in self._post_processors:
            post_processor(args)

    def run_validators(self, args: argparse.Namespace) -> bool:
        '''Run validation checks on arguments, false if any fail'''
        for validator in self._validators:
            if not validator(args):
                return False

        return True

PROG_NAME = "subby"

class CommandParser:
    '''Class for parsing command line input '''

    def __init__(self, subcommands: list[Subcommand]) -> None:
        parser = argparse.ArgumentParser(
                prog = PROG_NAME,
                description = "Subtitle Editor")

        self._subparser = Subparser(parser)
        self._subcommands: dict[str, Subparser] = {}

        self._subparsers = parser.add_subparsers(
                description = "Valid subcommands",
                dest = "subcmd")

        for subcommand in subcommands:
            self.add_subcommand(subcommand)

    def add_subcommand(self, subcommand: Subcommand) -> None:
        '''Set flags for subcommand'''
        parser = self._subparsers.add_parser(
                subcommand.name,
                help = subcommand.helpstring)

        subparser = Subparser(parser)
        self._subcommands[subcommand.name] = subparser

        if subcommand.args is None:
            return

        for args in subcommand.args:
            if args == SUBCMD_INPUT_SINGLE:
                self.add_single_file_input(subcommand.name)

            elif args == SUBCMD_INPUT_MANY:
                self.add_multiple_file_input(subcommand.name)

            elif args == SUBCMD_OUTPUT:
                self.add_file_output_flags_for_subcommand(subcommand.name)

            elif isinstance(args, SubcommandArgument):
                args_, kwargs = args.params()
                parser.add_argument(*args_, **kwargs)

        if subcommand.validators is not None:
            for validator in subcommand.validators:
                subparser.add_validator(validator)

        if subcommand.post_processors is not None:
            for post_processor in subcommand.post_processors:
                subparser.add_post_processor(post_processor)

    def add_single_file_input(self, subcommand: str) -> None:
        '''Add flags and validators for single file input'''

        # TODO better help string for `input`
        helpstring = "The input file"
        use_ranges_help_string = "Enable parsing for ranges of lines or" \
                " timestamps"

        subparser = self._subcommands[subcommand]
        parser = subparser.parser
        validator = validate_input_filetype
        post_processor = parse_promised_filerange

        parser.add_argument("input", help = helpstring)
        parser.add_argument("-R", "--use-ranges", action = "store_true", \
                help = use_ranges_help_string)
        subparser.add_validator(validator)
        subparser.add_post_processor(post_processor)

    def add_multiple_file_input(self, subcommand: str) -> None:
        '''Add flags and validators for multiple file input'''

        # TODO better help string for `input`
        helpstring = "The input file"
        use_ranges_help_string = "Enable parsing for ranges of lines or" \
                " timestamps"

        subparser = self._subcommands[subcommand]
        parser = subparser.parser
        validator = validate_many_input_filetypes
        post_processor = parse_many_promised_fileranges

        parser.add_argument("input", nargs = '+', help = helpstring)
        parser.add_argument("-R", "--use-ranges", action = "store_true", \
                help = use_ranges_help_string)
        subparser.add_validator(validator)
        subparser.add_post_processor(post_processor)

    def add_file_output_flags_for_subcommand(self, subcommand: str) -> None:
        '''Add flags and validators for file output processing for a
        subcommand'''

        subparser = self._subcommands[subcommand]
        parser = subparser.parser
        group = parser.add_mutually_exclusive_group(required = True)

        group.add_argument(
                "-o",
                "--output",
                metavar = "output",
                nargs = "?",
                help = "The output file")

        group.add_argument(
                "-O",
                "--overwrite",
                action = "store_true",
                help = "Flag to specify overwriting the input file;" \
                        " conflicts with -o")

    def parse_args(self) -> argparse.Namespace | None:
        '''Parse CLI with post-processing and validators'''
        args = self._subparser.parse_args()
        self._subparser.run_post_processors(args)

        log_flags = LogFlags(name = PROG_NAME)
        args.log_formatter = LogFormatter(log_flags)
        args.log_formatter.set_as_global_logger()

        if not self._subparser.run_validators(args):
            return

        subcmd_subparser = self._subcommands.get(args.subcmd)
        if subcmd_subparser is not None:
            subcmd_subparser.run_post_processors(args)
            if not subcmd_subparser.run_validators(args):
                return

        return args

