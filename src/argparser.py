from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Iterable, Literal
import sys

from filerange import FileRange, filerange
from logger import LEVEL_INFO, LEVEL_QUIET, LEVEL_VERBOSE, LogFlags,\
        LogFormatter, error, warn, LEVEL_DEBUG

def validate_input_filetype(args: dict[str, Any]) -> bool:
    '''Validate `args.input`; return false to stop execution'''
    filename: str = args["input"].filename
    if not filename.endswith(".srt"):
        error(f"'{filename}' is not an srt file")
        if ':' in filename:
            warn("If you specified a range, use -R to enable range parsing")
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

def parse_promised_filerange(args: dict[str, Any]) -> None:
    '''Parse file input to FileRange depending on conditions'''
    if args["use-ranges"]:
        args["input"] = filerange(args["input"])

    else:
        args["input"] = FileRange(args["input"], None, None)

def parse_many_promised_fileranges(args: dict[str, Any]) -> None:
    '''Parse file input to FileRange conditionally for many inputs'''
    parse_fn: Callable[[str], FileRange]
    if args["use-ranges"]:
        parse_fn = lambda input_: filerange(input_)

    else:
        parse_fn = lambda input_: FileRange(input_, None, None)

    args["input"] = [parse_fn(value) for value in args["input"]]

def set_verbosity(args: dict[str, Any]) -> None:
    '''Determine logging level from flags'''
    if args["quiet"]:
        args["verbosity"] = LEVEL_QUIET
        return

    if args["debug"]:
        args["verbosity"] = LEVEL_DEBUG
        return

    if args["verbose"]:
        args["verbosity"] = LEVEL_VERBOSE
        return

    args["verbosity"] = LEVEL_INFO
    return

def parse_logging_level(args: dict[str, Any]) -> None:
    '''Set global logging functions and formatters'''
    set_verbosity(args)
    log_flags = LogFlags(name = PROG_NAME,
                         verbosity = args["verbosity"])
    log_formatter = LogFormatter(log_flags)
    args["log_formatter"] = log_formatter
    log_formatter.set_as_global_logger()

ValidatorType = Callable[[dict[str, Any]], bool]
ProcessorType = Callable[[dict[str, Any]], None]

class ArgumentType(Enum):
    Value = auto()
    Enable = auto()
    Disable = auto()
    Multiple = auto()

ARG_VALUE    = ArgumentType.Value
ARG_ENABLE   = ArgumentType.Enable
ARG_DISABLE  = ArgumentType.Disable
ARG_MULTIPLE = ArgumentType.Multiple

@dataclass
class Flag:
    '''Schema for representing subcommand arguments'''
    name: str
    shorthand: str | None = None
    helpstring: str = ""
    display_name: str | None = None
    type: ArgumentType = ARG_VALUE
    choices: tuple[str, ...] | None = None
    value_type: Any = str
    default: Any = None

@dataclass
class FlagGroup:
    """Represent logical group of arguments"""
    arguments: list[Flag]
    mutually_exclusive: bool = False
    validators: list[ValidatorType] | None = None
    post_processors: list[ProcessorType] | None = None

def print_flags_group() -> FlagGroup:
    '''Create flag grouping for printing and logging levels'''
    quiet_helpstring = "Print no output; use this if you batch commands"
    return FlagGroup(
            arguments = [
                Flag(name = "-verbose",
                     shorthand = "-V",
                     helpstring = "Enable verbose feedback",
                     type = ARG_ENABLE),
                Flag(name = "-debug",
                     helpstring = "Enable debug feedback",
                     type = ARG_ENABLE),
                Flag(name = "-quiet",
                     shorthand = "-q",
                     helpstring = quiet_helpstring,
                     type = ARG_ENABLE)
            ],
            post_processors = [parse_logging_level]
    )

SUBCMD_INPUT_SINGLE = "input_single"
SUBCMD_INPUT_MANY   = "input_many"
SUBCMD_OUTPUT       = "output"

@dataclass
class Subcommand:
    '''Schema for representing subcommands'''
    name: str
    helpstring: str
    function: Callable[[dict[str, Any]], None] | None = None
    args: list[Flag | FlagGroup | Literal["input_single", "input_many",\
            "output"]] | None = None
    validators: list[ValidatorType] | None = None
    post_processors: list[ProcessorType] | None = None

    def add_flag(self, *args, **kwargs) -> Flag:
        '''Create subcommand flag; passes arguments to Flag contructor'''
        flag = Flag(*args, **kwargs)
        if self.args is not None:
            self.args.append(flag)
        else:
            self.args = [flag]
        return flag

    def add_flag_group(self, group: FlagGroup) -> None:
        '''Add flag group to subcommand'''
        if self.args is not None:
            self.args.append(group)
        else:
            self.args = [group]

        # extract validators and post processors
        if group.validators is not None:
            if self.validators is None:
                self.validators = []

            self.validators += group.validators

        if group.post_processors is not None:
            if self.post_processors is None:
                self.post_processors = []

            self.post_processors += group.post_processors

    def add_validator(self, validator: ValidatorType) -> None:
        '''Add validator to subcommand'''
        if self.validators is not None:
            self.validators.append(validator)
        else:
            self.validators = [validator]

    def add_post_processor(self, post_processor: ProcessorType) -> None:
        '''Add post processor to subcommand'''
        if self.post_processors is not None:
            self.post_processors.append(post_processor)
        else:
            self.post_processors = [post_processor]

    def run_post_processors(self, args: dict[str, Any]) -> None:
        '''Perform post processing on arguments'''
        if self.post_processors is None:
            return

        for post_processor in self.post_processors:
            post_processor(args)

    def run_validators(self, args: dict[str, Any]) -> bool:
        '''Run validation checks on arguments, False if any fail'''
        if self.validators is None:
            return True # no validators to check, so validation succeeds

        for validator in self.validators:
            if not validator(args):
                return False

        return True

class CommandLineArgumentError(Exception):
    pass

def parser_assert(expr: bool, msg: str, *args):
    '''Raises CommandLineArgumentError if expr is False'''
    if not expr:
        raise CommandLineArgumentError(msg.format(*args))

class ArgumentPool:
    """Represents a parsing pool of arguments and desired data structures, when
    parsing command line input"""
    def __init__(self, subparser: Subcommand | None = None) -> None:
        self._subcommands: list[Subcommand] = []
        self._arguments: dict[str, Flag] = {}
        self._names_map: dict[str, str] = {}
        self._positional_args: list[str] = []

        self.groups: list[dict[str, Any]] = []

        if subparser is not None:
            self.pool_subparser(subparser)

    def _append_argument(self, argument: Flag) -> str:
        """Add argument to pool; return registered name"""
        # argument is not a flag
        if not argument.name.startswith("-"):
            self._positional_args.append(argument.name)
            self._arguments[argument.name] = argument
            return argument.name

        # argument is a flag
        name: str = argument.name[1:] # skip dash
        if argument.shorthand is not None:
            # create mapping for short name to long name
            shorthand = argument.shorthand[1:] # skip dash
            self._names_map[shorthand] = name

        self._arguments[name] = argument
        return name

    def _extract_group(self, group: FlagGroup) -> None:
        """Extract arguments from group"""
        group_data = {
                "mutually_exclusive": group.mutually_exclusive,
                "members" : []
                }

        for argument in group.arguments:
            name = self._append_argument(argument)
            group_data["members"].append(name)

        self.groups.append(group_data)

    def pool_subparser(self, subparser: Subcommand) -> None:
        """Adds subparser data to pool"""
        self._subcommands.append(subparser)
        if subparser.args is None:
            return

        for argument in subparser.args:
            if isinstance(argument, FlagGroup):
                self._extract_group(argument)
                continue

            if isinstance(argument, str):
                continue

            self._append_argument(argument)

    def next_positional_arg(self) -> Flag:
        """Pop argument name from positional queue

        Exception if there are no more positional arguments to parse"""
        parser_assert(len(self._positional_args) != 0,
                      "Too many positional arguments provided")

        param = self._positional_args[0]
        self._positional_args.pop(0)
        return self.get_flag(param)

    def positional_arguments(self) -> list[str]:
        '''Return a list of remaining positional arguments'''
        return list(self._positional_args)

    def get_flag(self, flag_name: str) -> Flag:
        """Return structure data for flag

        Exception if flag name is unknown"""
        flag: Flag | None
        flag_name = flag_name.lstrip("-")
        long_name = self._names_map.get(flag_name)

        parser_assert(flag_name not in self._positional_args,
                      "{} is a positional argument and cannot be used as a"
                      " flag",
                      flag_name)

        if long_name is None:
            flag = self._arguments.get(flag_name)
        elif long_name in self._positional_args:
            raise CommandLineArgumentError(f"{flag_name} is a positional"\
                    " argument and cannot be used as a flag")
        else:
            flag = self._arguments.get(long_name)

        if flag is None:
            raise CommandLineArgumentError(f"Unknown flag {flag_name}")

        return flag

    def get_flags(self) -> list[Flag]:
        '''Return a list of currently pooled flags and arguments'''
        return list(self._arguments.values())

    def flag_defaults(self) -> dict[str, Any]:
        '''Return a mapping of every flag to its default value'''
        defaults: dict[str, Any] = {}
        for flag_name, flag in self._arguments.items():
            if flag.type == ARG_ENABLE:
                defaults[flag_name] = False
                continue

            elif flag.type == ARG_DISABLE:
                defaults[flag_name] = True
                continue

            elif flag.default is None:
                continue

            value_type = flag.value_type
            defaults[flag_name] = value_type(flag.default)

        return defaults

    def mutually_exclusive_groups(self) -> Iterable[list[str]]:
        '''Return a Iterable of each mutually exclusive group'''
        return (group["members"]
                for group in self.groups
                if group["mutually_exclusive"])

PROG_NAME = "subby"

class CommandParser:
    '''Class for parsing command line input

    Constructor Parameters for `options`:
        `no_print_flags` bool: if True, print flags will not be added to the
            command line parser (defaults to False)
        `program_name` str: reported program name in help strings
        `description` str: reported program description in help strings
    '''

    def __init__(self, subcommands: list[Subcommand], **options) -> None:
        self.program_name = options.get("program_name", PROG_NAME)
        self.description = options.get("description", "Subtitle Editor")

        self._root_command = Subcommand(self.program_name, self.description)
        self._subcommands: dict[str, Subcommand] = {}

        if not options.get("no_print_flags", False):
            self._root_command.add_flag_group(print_flags_group())

        for subcommand in subcommands:
            self.add_subcommand(subcommand)

        # initialise state for parsing
        self.args: list[str] = []
        self.pool = ArgumentPool(self._root_command)
        self.intermediates: dict[str, tuple[str, ...]] = {}
        self.parsed: dict[str, Any] = {}
        self.subcmd: str | None = None

        self.arg = ""
        self.current_flag: Flag | None = None
        self.current_flag_args: list[str] = []
        #self.pair_separator = ':'

    def strip_parsed_flag_keys(self) -> None:
        '''Strip flag keys of leading dashes'''
        self.parsed = {
                key.lstrip("-"): value
                for key, value in self.parsed.items() }

    def process_arguments(self):
        while len(self.args) > 0:
            self.arg = self.args[0]
            self.args.pop(0)
            next_action = self._detect_arg_type(self.arg)
            next_action()

    def parse_args(self,
                   args_in: list[str] | None = None
                   ) -> dict[str, Any] | None:
        '''Parse CLI input'''
        return self.parse_args_2(args_in)

    def parse_args_2(self,
                     args_in: list[str] | None = None
                     ) -> dict[str, Any] | None:
        '''Parse CLI input'''

        if args_in is None:
            self.args = sys.argv[1:]
        else:
            self.args = args_in

        # detect help input
        for help_flag in ('-h', '-help', '--help'):
            if help_flag in self.args:
                return self.print_help()

        # process argument
        self.process_arguments()

        # group mutual exclusion
        for group in self.pool.mutually_exclusive_groups():
            conflicts = [flag
                         for flag in self.intermediates.keys()
                         if flag.lstrip("-") in group]

            parser_assert(len(conflicts) <= 1,
                          "The following flags conflict: {}",
                          ", ".join(conflicts))

        # flag processing
        self._set_default_positionals()

        for arg_name, intermediate in self.intermediates.items():
            self._convert_intermediate(arg_name, intermediate)

        # combine with defaults, parsed values taking priority
        self.parsed = self.pool.flag_defaults() | self.parsed
        #self.parsed = {**self.pool.flag_defaults(), **self.parsed}

        # prepare parsed flags for post-processing and validation
        self.strip_parsed_flag_keys()
        self.parsed["subcmd"] = self.subcmd

        # post-processing and validation
        for subcommand in self.pool._subcommands:
            subcommand.run_post_processors(self.parsed)

        for subcommand in self.pool._subcommands:
            if not subcommand.run_validators(self.parsed):
                return None

        return self.parsed

    def _convert_choices(self,
                         arg_name: str,
                         intermediate: tuple[str, ...],
                         choices: tuple[str, ...]) -> None:
        '''Converts choice intermediate'''
        parser_assert(len(intermediate) == 1,
                      f"Unknown error parsing {arg_name}")

        value: str = intermediate[0]
        parser_assert(value in choices,
                      f"Error: {value} is not valid for {arg_name}")

        self.parsed[arg_name] = value

    def _convert_value_type(self,
                            arg_name: str,
                            intermediate: tuple[str, ...],
                            value_type: Any
                            ) -> tuple[Any]:
        '''Convert intermediate into specified value type; returns coverted
        values'''
        try:
            return tuple(value_type(value) for value in intermediate)
        except ValueError:
            raise CommandLineArgumentError(
                    f"Invalid value for {arg_name}")

    def _convert_intermediate(
            self, arg_name: str, intermediate: tuple[str, ...]):
        '''Converts intermediate and adds to parsed'''
        flag = self.pool.get_flag(arg_name)
        if flag.choices is not None:
            self._convert_choices(arg_name, intermediate, flag.choices)

        elif flag.value_type is str and flag.type == ARG_VALUE:
            parser_assert(len(intermediate) == 1,
                          f"Unknown error parsing {arg_name}")
            self.parsed[arg_name] = intermediate[0]

        elif flag.value_type is str and flag.type == ARG_MULTIPLE:
            self.parsed[arg_name] = intermediate

        elif flag.type == ARG_VALUE:
            parser_assert(len(intermediate) == 1,
                          f"Unknown error parsing {arg_name}")
            self.parsed[arg_name] = self._convert_value_type(
                    arg_name, intermediate, flag.value_type)[0]

        elif flag.type == ARG_MULTIPLE:
            self.parsed[arg_name] = self._convert_value_type(
                    arg_name, intermediate, flag.value_type)

        elif flag.type == ARG_DISABLE:
            self.parsed[arg_name] = False

        elif flag.type == ARG_ENABLE:
            self.parsed[arg_name] = True

    def _set_default_positionals(self):
        '''Assign default values to remaining positionals'''
        missing_positionals: list[Flag] = []
        try:
            while True:
                missing_positionals.append(self.pool.next_positional_arg())

        except CommandLineArgumentError:
            pass

        for flag in missing_positionals:
            parser_assert(flag.default is not None,
                          "No value provided for positional argument: {}",
                          flag.name)
            value_type = flag.value_type
            self.parsed[flag.name] = value_type(flag.default)

    def _detect_arg_type(self, arg: str):
        """Return next parser action from decoding argument type"""
        try:
            # optimise negative numbers by attempting to convert to number
            float(arg)
            return self._add_argument
        except ValueError:
            pass

        if arg in ("-h", "-help", "--help"):
            # skip help flag, this is handled elsewhere
            return lambda: None
        elif arg in self._subcommands.keys():
            return self._set_subcommand
        elif not arg.startswith("-"):
            return self._add_argument
        elif arg == "-":
            # this represents the stdin/stdout; so not a flag
            return self._add_argument
        elif ':' in arg:
            # flag:value pair
            return self._split_flag_value_pair
        elif '=' in arg:
            # flag=value pair
            return self._split_flag_value_pair
        else:
            return self._set_flag

    def flag_helpstring(self, flag: Flag) -> str:
        '''Return detailed helpstring for flag'''
        if flag.type is ArgumentType.Value:
            return "\t{}{}\t{}{}".format(
                    flag.display_name
                    if flag.display_name is not None else flag.name,
                    ', {}'.format(flag.shorthand)
                    if flag.shorthand is not None else '',
                    flag.helpstring,
                    '\n\t\t({})'.format(flag.default)
                    if flag.default is not None else '')

        elif flag.type in (ArgumentType.Enable, ArgumentType.Disable):
            return "\t{}{}\t{}".format(
                    flag.display_name
                    if flag.display_name is not None else flag.name,
                    ', {}'.format(flag.shorthand)
                    if flag.shorthand is not None else '',
                    flag.helpstring)

        elif flag.type is ArgumentType.Multiple:
            return "\t{}{}\t{}{}".format(
                    flag.display_name
                    if flag.display_name is not None else flag.name,
                    ', {}'.format(flag.shorthand)
                    if flag.shorthand is not None else '',
                    flag.helpstring,
                    '\n\t\t({})'.format(flag.default)
                    if flag.default is not None else '')

        return ''

    def cli_flag_helpstring(self, flag: Any) -> str:
        '''Return cli for flag or flag group'''
        flags: FlagGroup
        if isinstance(flag, Flag):
            flags = FlagGroup([flag])
        elif isinstance(flag, FlagGroup):
            flags = flag
        else:
            return ''

        return "{}{}{}".format(
                '[' if flags.mutually_exclusive else '{',
                ' | '.join(
                    flag.shorthand
                    if flag.shorthand is not None
                    else flag.name
                    for flag in flags.arguments),
                ']' if flags.mutually_exclusive else '}')

    def print_general_help(self) -> None:
        '''Print general help string with detail about subcommands'''
        prog_name = self._root_command.name
        description = self._root_command.helpstring

        cli_helpstr = '{} command options...'.format(
                prog_name)

        helpstr = "{}\n\nSubcommands:\n{}\n".format(
                description,
                '\n'.join(
                    '\t{}\t{}'.format(
                        subcommand.name,
                        subcommand.helpstring)
                    for subcommand in self._subcommands.values()))

        print(cli_helpstr)
        print(helpstr)

    def print_help(self) -> None:
        '''Print help string'''
        self.process_arguments()
        subcmd = self.subcmd
        if subcmd is None:
            return self.print_general_help()

        args = list(self._root_command.args
                    if self._root_command.args is not None
                    else [])

        help_pool = ArgumentPool(self._root_command)

        subcommand = self._subcommands[subcmd]
        help_pool.pool_subparser(subcommand)
        args += list(subcommand.args
                     if subcommand.args is not None
                     else [])

        prog_name = self._root_command.name
        flag_dict: dict[str, Flag] = {
                flag.name: flag
                for flag in help_pool.get_flags() }
        positionals = help_pool.positional_arguments()

        def is_flag(flag: Any):
            if isinstance(flag, Flag):
                if flag.name in positionals:
                    return False

            return True

        def format_flag_display(flag: Flag) -> str:
            return "{}{}".format(
                    flag.display_name
                    if flag.display_name is not None else flag.name,
                    '...' if flag.type is ArgumentType.Multiple else '')

        flags: list[Flag | FlagGroup | str] = [
                flag
                for flag in args
                if is_flag(flag)]

        display_name_map: dict[str, str] = {
                flag.name : format_flag_display(flag)
                for flag in flag_dict.values()}

        cli_helpstr = "{} {} {} {}".format(
                prog_name,
                subcmd,
                ' '.join(
                    display_name_map[flag]
                    for flag in positionals),
                ' '.join(
                    self.cli_flag_helpstring(flag)
                    for flag in flags))

        description = "{}\n".format(subcommand.helpstring)

        positional_help = "Parameters:\n{}\n".format(
                '\n'.join(
                    self.flag_helpstring(flag_dict[flag_name])
                    for flag_name in positionals))

        flag_help = "Flags:\n{}\n".format(
                '\n'.join(
                    self.flag_helpstring(flag)
                    for flag in flag_dict.values()
                    if is_flag(flag)))

        print(cli_helpstr)
        print(description)
        print(positional_help)
        print(flag_help)

    def _set_subcommand(self):
        '''Assign subcommand from cli parsing'''
        self.subcmd = self.arg
        self.pool.pool_subparser(self._subcommands[self.subcmd])

    def _add_argument(self) -> None:
        '''Assign arg value to current flag; fetch flag if necessary'''
        if self.current_flag is None:
            self.current_flag = self.pool.next_positional_arg()
            self.current_flag_args = []

        self.current_flag_args.append(self.arg)
        if self.current_flag.type != ARG_MULTIPLE:
            self._store_parsed_flags_2(self.current_flag,
                                       self.current_flag_args)

            self.current_flag = None
            self.current_flag_args = []

    def _split_flag_value_pair(self) -> None:
        '''Split flag value pair and assign to parsed'''
        if ':' in self.arg:
            pair_separator = ':'
        elif '=' in self.arg:
            pair_separator = '='
        else:
            raise CommandLineArgumentError(
                    f"Error on flag-value pair: {self.arg}")

        split = self.arg.split(pair_separator, 1)
        parser_assert(len(split) != 1,
                      "Unknown error spltting flag-value pair {}",
                      self.arg)
        flag_name = split[0]
        value = split[1]
        parser_assert(len(value) != 0,
                      f"Value cannot be blank in pair: {self.arg}")

        if self.current_flag is not None:
            self._store_parsed_flags_2(
                    self.current_flag, self.current_flag_args)

        self.current_flag = self.pool.get_flag(flag_name)
        if self.current_flag.type == ARG_MULTIPLE:
            # list conversion to get around LiteralString mismatch
            # pylance being annoying; and fucking slow
            arg_list: list[str] = list(value.split(';'))
            self._store_parsed_flags_2(self.current_flag, arg_list)
            self.current_flag = None
            self.current_flag_args = []
            return

        # store flag-value pair
        self._store_parsed_flags_2(self.current_flag, [value])
        self.current_flag = None
        self.current_flag_args = []

    def _set_flag(self) -> None:
        '''Set the current flag'''
        if self.current_flag is not None:
            self._store_parsed_flags_2(
                    self.current_flag, self.current_flag_args)

        self.current_flag = self.pool.get_flag(self.arg)
        self.current_flag_args = []

        parser_assert(self.current_flag is not None,
                      "Unknown error parsing next flag: {}",
                      self.current_flag)

        # for switches, skip taking arguments
        # boolean values are added later in the parsing process
        if self.current_flag.type in (ARG_ENABLE, ARG_DISABLE):
            self._store_parsed_flags_2(self.current_flag, [])
            self.current_flag = None

    def add_subcommand(self, subcommand: Subcommand) -> None:
        '''Set flags for subcommand'''
        self._subcommands[subcommand.name] = subcommand

        if subcommand.args is None:
            return

        for index, args in enumerate(subcommand.args):
            # remove literal subcommand and insert actual flags
            if args == SUBCMD_INPUT_SINGLE:
                subcommand.args.pop(index)
                self.sub_add_single_file_input(subcommand.name)

            elif args == SUBCMD_INPUT_MANY:
                subcommand.args.pop(index)
                self.sub_add_multiple_file_input(subcommand.name)

            elif args == SUBCMD_OUTPUT:
                subcommand.args.pop(index)
                self.sub_add_file_output_flags_for_subcommand(subcommand.name)

    def sub_add_single_file_input(self, subcommand_name: str) -> None:
        '''Add flags and validators for single file input'''

        # TODO better help string for `input`
        helpstring = "The input file"
        use_ranges_help_string = "Enable parsing for ranges of lines or" \
            " timestamps"

        subcommand = self._subcommands[subcommand_name]
        validator = validate_input_filetype
        post_processor = parse_promised_filerange

        subcommand.add_flag("input", helpstring = helpstring)
        subcommand.add_flag(
            "-use-ranges",
            shorthand = "-R",
            type = ARG_ENABLE,
            helpstring = use_ranges_help_string)

        subcommand.add_validator(validator)
        subcommand.add_post_processor(post_processor)

    def sub_add_multiple_file_input(self, subcommand_name: str) -> None:
        '''Add flags and validators for multiple file input'''

        # TODO better help string for `input`
        helpstring = "The input file"
        use_ranges_help_string = "Enable parsing for ranges of lines or" \
            " timestamps"

        subcommand = self._subcommands[subcommand_name]
        validator = validate_many_input_filetypes
        post_processor = parse_many_promised_fileranges

        subcommand.add_flag(
            "input",
            type = ARG_MULTIPLE,
            helpstring = helpstring)

        subcommand.add_flag(
            "-use-ranges",
            shorthand = "-R",
            type = ARG_ENABLE,
            helpstring = use_ranges_help_string)

        subcommand.add_validator(validator)
        subcommand.add_post_processor(post_processor)

    def sub_add_file_output_flags_for_subcommand(
            self, subcommand_name: str) -> None:
        '''Add flags and validators for file output processing for a
        subcommand_name'''

        subcommand = self._subcommands[subcommand_name]
        group: list[Flag] = []

        group.append(Flag(
            "-output",
            shorthand = "-o",
            helpstring = "The output file"))

        group.append(Flag(
            "-overwrite",
            shorthand = "-O",
            type = ARG_ENABLE,
            helpstring = "Flag to specify overwriting the input file;"\
                " conflicts with -o"))

        # create mutually exclusive group
        subcommand.add_flag_group(FlagGroup(group, True))

    def _store_parsed_flags_2(self, flag: Flag, flag_args: list[str]) -> None:
        """Performs all checks to store flags in parsed flags"""
        if flag.name in self.intermediates.keys():
            new_flag_args = flag_args
            flag_args = list(self.intermediates[flag.name])
            flag_args += new_flag_args

        self.intermediates[flag.name] = tuple(flag_args)

