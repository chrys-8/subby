import argparse
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Sequence

from logger import parse_logging_level

ValidatorType = Callable[[dict[str, Any]], bool]
ProcessorType = Callable[[dict[str, Any]], None]

def program_name_assigner(prog_name: str) -> ProcessorType:
    '''Return a callable that assigns program name to argument dictionary'''
    def assigner(args: dict[str, Any]) -> None:
        args["prog"] = prog_name
        return

    return assigner

class ParameterType(Enum):
    Value    = auto()
    Enable   = auto()
    Disable  = auto()
    Optional = auto()
    Multiple = auto()

ARG_VALUE    = ParameterType.Value
ARG_ENABLE   = ParameterType.Enable
ARG_DISABLE  = ParameterType.Disable
ARG_OPTIONAL = ParameterType.Optional
ARG_MULTIPLE = ParameterType.Multiple

@dataclass
class Parameter:
    '''Schema for representing subcommand arguments'''
    name: str
    helpstring: str
    long_name: str | None = None
    display_name: str | None = None
    type: ParameterType = ARG_VALUE
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
class MutuallyExclusiveGroup:
    '''Represents a group of subcommand arguments that are mutually
    exclusive'''
    parameters: list[Parameter]
    required: bool = False

@dataclass
class ParameterGroup:
    '''Schema for representing grouped subcommand arguments'''
    parameters: list[Parameter | MutuallyExclusiveGroup]
    title: str | None = None
    description: str | None = None
    deferred_validators: list[ValidatorType] | None = None
    deferred_post_processers: list[ProcessorType] | None = None

@dataclass
class Command:
    '''Schema for representing subcommands'''
    name: str
    helpstring: str
    function: Callable[[dict[str, Any]], None]
    parameters: list[Parameter | MutuallyExclusiveGroup |
                     ParameterGroup ] | None = None
    validators: list[ValidatorType] | None = None
    post_processors: list[ProcessorType] | None = None

ParserLike = argparse.ArgumentParser | argparse._ArgumentGroup | \
        argparse._MutuallyExclusiveGroup

def add_params_to_parserlike(
        params: Sequence[Parameter] | Parameter,
        parser: ParserLike) -> None:
    '''Add many parameters to a parserlike object'''
    if isinstance(params, Parameter):
        params = (params,)

    for param in params:
        parser_args, parser_kwargs = param.params()
        parser.add_argument(*parser_args, **parser_kwargs)

class Parser:
    '''Wrap ArgumentParser with validators and post processors'''

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        # TODO refactor to construct ArgumentParser in constructor
        self.parser = parser
        self._validators: list[ValidatorType] = []
        self._post_processors: list[ProcessorType] = []

    def add_parameter(self, param: Parameter) -> None:
        '''Add parameter to parser'''
        add_params_to_parserlike(param, self.parser)

    def add_mutually_exclusive_group(
            self, param_group: MutuallyExclusiveGroup) -> None:
        '''Add group of mutually exclusive parameters to parser'''
        group = self.parser.add_mutually_exclusive_group(
                required = param_group.required)
        add_params_to_parserlike(param_group.parameters, group)

    def add_group(self, param_group: ParameterGroup) -> None:
        '''Add grouped parameters to parser'''
        # for groups with no title, add directly to command root parser
        if param_group.title is None:
            group = self.parser
        else:
            group = self.parser.add_argument_group(param_group.title,
                                                   param_group.description)

        for argument in param_group.parameters:
            if isinstance(argument, Parameter):
                add_params_to_parserlike(argument, group)

            elif isinstance(argument, MutuallyExclusiveGroup):
                mut_group = group.add_mutually_exclusive_group(
                        required = argument.required)
                add_params_to_parserlike(argument.parameters, mut_group)

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
        # TODO extend to accept args as a function parameter
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

class CommandLine:
    '''Class for parsing command line input

    Constructor Parameters:
        `prog_name` str: the name of the application for help strings and
            logging

        `description` str: a brief description of what the program does

        `no_print_flags` bool: if True, print flags will not be added to the
            command line parser (defaults to False)
    '''

    def __init__(self, subcommands: list[Command], **options) -> None:
        prog_name = options.get("prog_name", "program")
        description = options.get("description", "No description")
        parser = argparse.ArgumentParser(
                prog = prog_name,
                description = description)

        self._parser = Parser(parser)
        self._commands: dict[str, Parser] = {}

        if not options.get("no_print_flags", False):
            self._parser.add_post_processor(program_name_assigner(prog_name))
            self.add_print_flags()

        self._subparsers = parser.add_subparsers(
                description = "Valid subcommands",
                dest = "subcmd")

        for subcommand in subcommands:
            self.add_command(subcommand)

    def add_print_flags(self) -> None:
        """Set flags for printing and logging levels"""
        # TODO refactor to param group
        parser = self._parser.parser

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

        self._parser.add_post_processor(parse_logging_level)

    def add_command(self, command: Command) -> None:
        '''Set flags for command'''
        subparser = self._subparsers.add_parser(
                command.name,
                help = command.helpstring)

        parser = Parser(subparser)
        self._commands[command.name] = parser

        if command.parameters is None:
            return

        for args in command.parameters:
            if isinstance(args, Parameter):
                parser.add_parameter(args)

            elif isinstance(args, MutuallyExclusiveGroup):
                parser.add_mutually_exclusive_group(args)

            elif isinstance(args, ParameterGroup):
                parser.add_group(args)

        if command.validators is not None:
            for validator in command.validators:
                parser.add_validator(validator)

        if command.post_processors is not None:
            for post_processor in command.post_processors:
                parser.add_post_processor(post_processor)

    def parse_args(self) -> dict[str, Any] | None:
        '''Parse CLI with post-processing and validators'''
        parsed_args = self._parser.parse_args()
        self._parser.run_post_processors(parsed_args)

        if not self._parser.run_validators(parsed_args):
            return

        subcmd_subparser = self._commands.get(parsed_args["subcmd"])
        if subcmd_subparser is not None:
            subcmd_subparser.run_post_processors(parsed_args)
            if not subcmd_subparser.run_validators(parsed_args):
                return

        return parsed_args

