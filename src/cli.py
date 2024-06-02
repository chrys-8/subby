<<<<<<< HEAD
import argparse
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Sequence
=======
from dataclasses import dataclass
>>>>>>> 3c378df0b457217c2bc8c980ec3a0c163a416c48

def is_float(value: str) -> bool:
    '''Return True if value is convertable to a float'''
    try:
        float(value)
    except ValueError:
        return False

    return True

class CommandLineError(Exception):
    pass

@dataclass()
class CommandSchema:
    registered_flags: list[str]
    shorthand_map: dict[str, str]

    def add_flag(self, name: str, shorthand: str | None = None) -> None:
        '''Add flag to schema'''
        self.registered_flags.append(name)
        if shorthand is not None:
            self.registered_flags.append(shorthand)
            self.add_shorthand(name, shorthand)

    def add_shorthand(self, name: str, shorthand: str) -> None:
        '''Add shorthand to map'''
        self.shorthand_map[shorthand] = name

    def map_shorthand(self, shorthand: str) -> str | None:
        '''Return long name for shorthand'''
        if shorthand not in self.shorthand_map.keys():
            return None

        return self.shorthand_map[shorthand]

@dataclass()
class CommandLine:
    positional_arguments: list[str]
    named_arguments: dict[str, tuple[str, ...]]
    flags: dict[str, bool]

def is_positional(arg: str) -> bool:
    '''Return True if arg is a positional argument'''
    if is_float(arg):
        return True

    if arg.startswith("-"):
        return False

    return True

def is_next_positional(args: list[str]) -> bool:
    '''Return True if next arg is a positional argument'''
    if len(args) == 0:
        return False

    return is_positional(args[0])

def format_arg(arg: str) -> str:
    '''Format argument for parsing'''
    return arg.replace("-", "_").lstrip("_")

def parse_cli(args_: list[str], schema: CommandSchema | None = None) -> CommandLine:
    '''Parse the command line input into a CommandLine object'''
    if schema is None:
        schema = CommandSchema([], {})

    args = args_.copy()     # leave the input sequence unaltered
    command_line = CommandLine([], {}, {})
    while len(args) != 0:
        arg = args.pop(0)
        formatted = format_arg(arg)
        if (long_name := schema.map_shorthand(formatted)) is not None:
            formatted = long_name

        if is_positional(arg):
            command_line.positional_arguments.append(arg)

        elif formatted in schema.registered_flags:
            command_line.flags[formatted] = True

        elif arg.startswith("--") and is_next_positional(args):
            # long named argument
            command_line.named_arguments[formatted] = (args.pop(0), )

        elif arg.startswith("-") and is_next_positional(args):
            # shorthand named argument
            ...

        else:
            raise CommandLineError(f"Unknown flag: {arg}")

    raise NotImplementedError

