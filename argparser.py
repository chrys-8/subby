import argparse
from typing import Callable

def validate_input_filetype(args: argparse.Namespace) -> bool:
    '''Validate `args.input`; return false to stop execution'''

    # TODO implement force
    if not args.input.endswith(".srt"):
        print(f"'{args.input}' is not an srt file (--force (not" \
                " implemented))")
        return False

    return True

def validate_output_flags(args: argparse.Namespace) -> bool:
    '''Validate ouput arguments; return false to stop execution'''

    if args.output is None and not args.overwrite:
        print("Please specify an output file with -o, or use the" \
                " --overwrite flag")
        return False

    return True

class Commands:
    '''Class `Command` for parsing command line input '''

    def __init__(self, *args, **kwargs) -> None:
        self._parser = argparse.ArgumentParser(
                *args,
                prog = "subby",
                description = "Subtitle Editor",
                **kwargs)

        self._validators: list[Callable[[argparse.Namespace], bool]] = []

        self._parser.add_argument(
                "input",
                help = "The input file")

        self._validators.append(validate_input_filetype)

        self._parser.add_argument(
                "-o",
                "--output",
                nargs = "?",
                help = "The output file")

        self._validators.append(validate_output_flags)

        self._parser.add_argument(
                "-d",
                "--delay",
                type = int,
                default = 0,
                help = "Delay subtitle lines in milliseconds")

        self._parser.add_argument(
                "-b",
                "--begin",
                type = int,
                default = 0,
                help = "Line index to being delay from")

        self._parser.add_argument(
                "--overwrite",
                action = "store_true",
                help = "Flag to specify overwriting the input file;" \
                        " ignores -o")

    def parse_args(self) -> argparse.Namespace | None:
        args =  self._parser.parse_args()
        for validator in self._validators:
            if not validator(args):
                return None

        return args

