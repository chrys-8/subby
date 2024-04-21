import argparse
from dataclasses import dataclass
from typing import Any, Callable, Literal, Type

from filerange import filerange

def validate_input_filetype(args: argparse.Namespace) -> bool:
    '''Validate `args.input`; return false to stop execution'''

    # TODO implement force
    if not args.input.filename.endswith(".srt"):
        print(f"'{args.input.filename}' is not an srt file")
        return False

    return True

def validate_many_input_filetypes(args: argparse.Namespace) -> bool:
    '''Validate srt filetypes in `args.input`; false if invalid'''

    # TODO implement force
    for filerange_ in args.input:
        if not filerange_.filename.endswith(".srt"):
            print(f"'{filerange_.filename} is not an srt file")
            return False

    return True

ValidatorType = Callable[[argparse.Namespace], bool]

def subcommand_validator(
        validator: ValidatorType,
        subcommand: str
        ) -> ValidatorType:
    '''Make validator function for specified subcommand'''

    def wrapped(args: argparse.Namespace) -> bool:
        if args.subcmd != subcommand:
            return True # do not evaluate for other subcommands

        return validator(args)

    return wrapped

ARG_VALUE   = "value"
ARG_ENABLE  = "enable"
ARG_DISABLE = "disable"

@dataclass
class SubcommandArgument:
    '''Schema for representing subcommand arguments'''
    name: str
    helpstring: str
    long_name: str | None = None
    display_name: str | None = None
    type: Literal["value", "enable", "disable"] = ARG_VALUE
    choices: tuple[str, ...] | None = None
    value_type: Type = str

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

        if self.type == ARG_ENABLE:
            options["action"] = "store_true"

        elif self.type == ARG_DISABLE:
            options["action"] = "store_false"

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

class Commands:
    '''Class for parsing command line input '''

    def __init__(self, subcommands: list[Subcommand]) -> None:
        # TODO better help string
        self._parser = argparse.ArgumentParser(
                prog = "subby",
                description = "Subtitle Editor")

        self._validators: list[ValidatorType] = []
        self._subcommands: dict[str, argparse.ArgumentParser] = {}

        self._subparsers = self._parser.add_subparsers(
                description = "Valid subcommands",
                dest = "subcmd")

        for subcommand in subcommands:
            self.add_subcommand(subcommand)

        #self.add_subcommand_delay()

    def add_subcommand(self, subcommand: Subcommand) -> None:
        '''Set flags for subcommand'''
        parser = self._subparsers.add_parser(
                subcommand.name,
                help = subcommand.helpstring)

        self._subcommands[subcommand.name] = parser

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

    def add_subcommand_delay(self) -> None:
        '''Set flags for delay subcommand'''

        subcommand = "delay"
        helpstring = "Specify unit of delay (default millisecond)"

        delay_parser = self._subparsers.add_parser(
                subcommand,
                help = helpstring
                )

        self._subcommands[subcommand] = delay_parser

        # TODO abstract? Commands class perhaps shouldn't be tied to the
        # implementation of subcommands, and perhaps should deal with generic
        # flag parsing, given specific input
        self.add_single_file_input(subcommand)
        self.add_file_output_flags_for_subcommand(subcommand)

        delay_parser.add_argument(
                "-u",
                "--unit",
                choices = ("millisecond", "second", "minute", "ms", "s"),
                help = helpstring)

        # default behaviour is add delay to specifid range and encode the
        # entire file, with only the range modified
        delay_parser.add_argument(
                "-x",
                "--exclusive",
                action = "store_true",
                help = "Encode only the specified range; use this to trim " \
                        "files")

        delay_parser.add_argument(
                "delay",
                metavar = "delay_by",
                type = int,
                help = "Delay subtitle lines (default unit milliseconds")

    def add_single_file_input(self, subcommand: str) -> None:
        '''Add flags and validators for single file input'''

        # TODO better help string for `input`
        helpstring = "The input file"

        parser = self._subcommands[subcommand]
        validator = subcommand_validator(validate_input_filetype, subcommand)

        parser.add_argument("input", type = filerange, help = helpstring)
        self._validators.append(validator)

    def add_multiple_file_input(self, subcommand: str) -> None:
        '''Add flags and validators for multiple file input'''

        # TODO better help string for `input`
        helpstring = "The input file"

        parser = self._subcommands[subcommand]
        validator = subcommand_validator(validate_many_input_filetypes,
                                         subcommand)

        parser.add_argument("input",
                            type = filerange,
                            nargs = '+',        # yields a list
                            help = helpstring)

        self._validators.append(validator)

    def add_file_output_flags_for_subcommand(self, subcommand: str) -> None:
        '''Add flags and validators for file output processing for a subcommand'''

        parser = self._subcommands[subcommand]
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
        args =  self._parser.parse_args()
        for validator in self._validators:
            if not validator(args):
                return None

        return args

