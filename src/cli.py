import argparse
from dataclasses import dataclass
from typing import Any, Callable, Literal, Sequence

from logger import parse_logging_level

# TODO rename EVERYTHING
#   too much ambiguity between subcommand arguments/subcommand parameters
#   weird class names: e.g. Subparser wraps argparse.ArgumentParser, but can
#   represent a parser at any level, not just subparser level

ValidatorType = Callable[[dict[str, Any]], bool]
ProcessorType = Callable[[dict[str, Any]], None]

def program_name_assigner(prog_name: str) -> ProcessorType:
    '''Return a callable that assigns program name to argument dictionary'''
    def assigner(args: dict[str, Any]) -> None:
        args["prog"] = prog_name
        return

    return assigner

ARG_VALUE    = "value"
ARG_ENABLE   = "enable"
ARG_DISABLE  = "disable"
ARG_OPTIONAL = "optional"
ARG_MULTIPLE = "multiple"

@dataclass
class SubcommandArgument:
    '''Schema for representing subcommand arguments'''
    name: str
    helpstring: str
    long_name: str | None = None
    display_name: str | None = None
    type: Literal["value", "enable", "disable", "optional", "multiple"] =\
            ARG_VALUE
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

        elif self.type == ARG_MULTIPLE:
            options["nargs"] = "+"

        return tuple(names), options

@dataclass
class MutuallyExclusiveSubArgGroup:
    '''Represents a group of subcommand arguments that are mutually
    exclusive'''
    arguments: list[SubcommandArgument]
    required: bool = False

@dataclass
class SubcommandArgumentGroup:
    '''Schema for representing grouped subcommand arguments'''
    arguments: list[SubcommandArgument | MutuallyExclusiveSubArgGroup]
    title: str | None = None
    description: str | None = None
    deferred_validators: list[ValidatorType] | None = None
    deferred_post_processers: list[ProcessorType] | None = None

@dataclass
class Subcommand:
    '''Schema for representing subcommands'''
    name: str
    helpstring: str
    function: Callable[[dict[str, Any]], None]
    args: list[SubcommandArgument | MutuallyExclusiveSubArgGroup |
               SubcommandArgumentGroup ] | None = None
    validators: list[ValidatorType] | None = None
    post_processors: list[ProcessorType] | None = None

ParserLike = argparse.ArgumentParser | argparse._ArgumentGroup | \
        argparse._MutuallyExclusiveGroup

def add_params_to_parserlike(
        params: Sequence[SubcommandArgument] | SubcommandArgument,
        parser: ParserLike) -> None:
    '''Add many parameters to a parserlike object'''
    if isinstance(params, SubcommandArgument):
        params = (params,)

    for param in params:
        args, kwargs = param.params()
        parser.add_argument(*args, **kwargs)

class Subparser:
    '''Wrap ArgumentParser with validators and post processors'''

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.parser = parser
        self._validators: list[ValidatorType] = []
        self._post_processors: list[ProcessorType] = []

    def add_argument(self, param: SubcommandArgument) -> None:
        add_params_to_parserlike(param, self.parser)

    def add_mutually_exclusive_group(
            self, param_group: MutuallyExclusiveSubArgGroup) -> None:
        '''Add group of mutually exclusive arguments to parser'''
        group = self.parser.add_mutually_exclusive_group(
                required = param_group.required)
        add_params_to_parserlike(param_group.arguments, group)

    def add_group(self, param_group: SubcommandArgumentGroup) -> None:
        '''Add grouped arguments to parser'''
        # for groups with no title, add directly to command root parser
        if param_group.title is None:
            group = self.parser
        else:
            group = self.parser.add_argument_group(param_group.title,
                                                   param_group.description)

        for argument in param_group.arguments:
            if isinstance(argument, SubcommandArgument):
                add_params_to_parserlike(argument, group)

            elif isinstance(argument, MutuallyExclusiveSubArgGroup):
                mut_group = group.add_mutually_exclusive_group(
                        required = argument.required)
                add_params_to_parserlike(argument.arguments, mut_group)

        if param_group.deferred_validators is not None:
            for validator in param_group.deferred_validators:
                self.add_validator(validator)

        if param_group.deferred_post_processers is not None:
            for post_processor in param_group.deferred_post_processers:
                self.add_post_processor(post_processor)

    def add_validator(self, validator: ValidatorType) -> None:
        '''Add validator to parser'''
        self._validators.append(validator)

    def add_post_processor(self, post_processor: ProcessorType) -> None:
        '''Add post_processor to parser'''
        self._post_processors.append(post_processor)

    def parse_args(self) -> dict[str, Any]:
        '''Yield arguments from command line parsing'''
        args = self.parser.parse_args()
        return args.__dict__

    def run_post_processors(self, args: dict[str, Any]) -> None:
        '''Perform post processing on arguments'''
        for post_processor in self._post_processors:
            post_processor(args)

    def run_validators(self, args: dict[str, Any]) -> bool:
        '''Run validation checks on arguments, false if any fail'''
        for validator in self._validators:
            if not validator(args):
                return False

        return True

class CommandParser:
    '''Class for parsing command line input

    Constructor Parameters:
        `prog_name` str: the name of the application for help strings and
            logging

        `description` str: a brief description of what the program does

        `no_print_flags` bool: if True, print flags will not be added to the
            command line parser (defaults to False)
    '''

    def __init__(self, subcommands: list[Subcommand], **options) -> None:
        prog_name = options.get("prog_name", "program")
        description = options.get("description", "No description")
        parser = argparse.ArgumentParser(
                prog = prog_name,
                description = description)

        self._subparser = Subparser(parser)
        self._subcommands: dict[str, Subparser] = {}

        if not options.get("no_print_flags", False):
            self._subparser.add_post_processor(program_name_assigner(prog_name))
            self.add_print_flags()

        self._subparsers = parser.add_subparsers(
                description = "Valid subcommands",
                dest = "subcmd")

        for subcommand in subcommands:
            self.add_subcommand(subcommand)

    def add_print_flags(self) -> None:
        """Set flags for printing and logging levels"""
        # TODO refactor to param group
        parser = self._subparser.parser

        parser.add_argument(
                "-V",
                "--verbose",
                action = "store_true",
                help = "Enable verbose feedback"
                )

        parser.add_argument(
                "--debug",
                action = "store_true",
                help = "Enable debug feedback"
                )

        parser.add_argument(
                "-q",
                "--quiet",
                action = "store_true",
                help = "Print no output; use this if you batch commands"
                )

        self._subparser.add_post_processor(parse_logging_level)

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
            if isinstance(args, SubcommandArgument):
                subparser.add_argument(args)

            elif isinstance(args, MutuallyExclusiveSubArgGroup):
                subparser.add_mutually_exclusive_group(args)

            elif isinstance(args, SubcommandArgumentGroup):
                subparser.add_group(args)

        if subcommand.validators is not None:
            for validator in subcommand.validators:
                subparser.add_validator(validator)

        if subcommand.post_processors is not None:
            for post_processor in subcommand.post_processors:
                subparser.add_post_processor(post_processor)

    def parse_args(self) -> dict[str, Any] | None:
        '''Parse CLI with post-processing and validators'''
        args = self._subparser.parse_args()
        self._subparser.run_post_processors(args)

        if not self._subparser.run_validators(args):
            return

        subcmd_subparser = self._subcommands.get(args["subcmd"])
        if subcmd_subparser is not None:
            subcmd_subparser.run_post_processors(args)
            if not subcmd_subparser.run_validators(args):
                return

        return args
