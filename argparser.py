import argparse
from typing import Callable

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

class Commands:
    '''Class for parsing command line input '''

    def __init__(self, *args, **kwargs) -> None:
        # TODO better help string
        self._parser = argparse.ArgumentParser(
                *args,
                prog = "subby",
                description = "Subtitle Editor",
                **kwargs)

        self._validators: list[ValidatorType] = []
        self._subcommands: dict[str, argparse.ArgumentParser] = {}

        self._subparsers = self._parser.add_subparsers(
                description = "Valid subcommands",
                dest = "subcmd")

        self.add_subcommand_display()
        self.add_subcommand_delay()

    def add_subcommand_display(self) -> None:
        '''Set flags for display subcommand'''

        subcommand = "display"
        helpstring = "Display information about subtitle file"

        display_parser = self._subparsers.add_parser(
                subcommand,
                help = helpstring)

        self._subcommands[subcommand] = display_parser

        display_parser.add_argument(
                "--long",
                action = "store_true",
                help = "Display detailed information")

        display_parser.add_argument(
                "--missing",
                action = "store_true",
                help = "Not implemented")

        self.add_single_file_input(subcommand)

    def add_subcommand_delay(self) -> None:
        '''Set flags for delay subcommand'''

        subcommand = "delay"
        helpstring = "Specify unit of delay (default millisecond)"
        delay_parser = self._subparsers.add_parser(subcommand)
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
                help = "Encode only the specified range; use this to trim files")

        delay_parser.add_argument(
                "delay",
                metavar = "delayBy",
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

