from dataclasses import astuple, dataclass
from typing import Callable

import term

class LogFunction:
    '''Wraps an output function for a logging level'''
    def __init__(self, function: Callable[[str], None]) -> None:
        self._function = function

    def __call__(self, output: str) -> None:
        '''Calls wrapped logging output function'''
        self._function(output)

LEVEL_DEBUG = -2
LEVEL_VERBOSE = -1
LEVEL_INFO = 0
LEVEL_WARN = 1
LEVEL_ERROR = 2

LEVELS = {
        LEVEL_DEBUG : {
            "mode": "debug",
            "display": "DBG",
            "control_seq": term.term_color_fg("green"),
            "reset_seq": term.term_color_fg("default")
            },
        LEVEL_VERBOSE : {
            "mode": "verbose",
            "display": "INFO",
            "control_seq": "",
            "reset_seq": term.term_color_fg("default")
            },
        LEVEL_INFO : {
            "mode": "info",
            "display": "INFO",
            "control_seq": "",
            "reset_seq": term.term_color_fg("default")
            },
        LEVEL_WARN: {
            "mode": "warn",
            "display": "WARNING",
            "control_seq": term.term_color_fg("yellow"),
            "reset_seq": term.term_color_fg("default")
            },
        LEVEL_ERROR: {
            "mode": "error",
            "display": "ERROR",
            "control_seq": term.term_color_fg("red"),
            "reset_seq": term.term_color_fg("default")
            }
        }

@dataclass
class Logger:
    '''Implements Logger levels for terminal feedback'''
    debug: LogFunction
    verbose: LogFunction
    info: LogFunction
    warn: LogFunction
    error: LogFunction

@dataclass
class LogFlags:
    '''Represents command line flags for logging'''
    name: str
    verbosity: int = 0
    use_term_colors: bool = True

global_logger: Logger | None = None

def debug(text: str) -> None:
    '''Run debug from global logger'''
    global global_logger
    if global_logger is not None:
        global_logger.debug(text)

def verbose(text: str) -> None:
    '''Run verbose from global logger'''
    global global_logger
    if global_logger is not None:
        global_logger.verbose(text)

def info(text: str) -> None:
    '''Run info from global logger'''
    global global_logger
    if global_logger is not None:
        global_logger.info(text)

def warn(text: str) -> None:
    '''Run warn from global logger'''
    global global_logger
    if global_logger is not None:
        global_logger.warn(text)

def error(text: str) -> None:
    '''Run error from global logger'''
    global global_logger
    if global_logger is not None:
        global_logger.error(text)

class LogFormatter:
    '''Implement formatting for logging output'''
    def __init__(self, flags: LogFlags) -> None:
        self.flags = flags

        self._log_buffer: list[str] = []

    def _create_log_function(self, **kwargs) -> LogFunction:
        '''Create log function from specified arguments

        There are two groups of parameters, log and print. When a parameter
        begins with *, this imples a separate parameter for each group.

        Parameters:
        - verbosity         : int required
        - *_time            : bool
        - *_use_prefix      : bool default True for log, False for print
        - prefix            : str
        - *_display_mode    : bool default False
        '''
        verbosity: int = kwargs["verbosity"]
        if verbosity < self.flags.verbosity:
            # runs quietly
            return LogFunction(lambda _: None)

        # TODO implement log_prefix and log_postfix
        print_prefix = ""
        print_postfix = ""

        # TODO implement *_time

        if self.flags.use_term_colors:
            print_prefix += LEVELS[verbosity]["control_seq"]
            print_postfix += LEVELS[verbosity]["reset_seq"]

        print_use_prefix = kwargs.get("print_use_prefix", False)
        if print_use_prefix:
            prefix = kwargs.get("prefix", self.flags.name)
            print_prefix += "[{}]".format(prefix)

        print_display_mode = kwargs.get("print_display_mode", False)
        if print_display_mode:
            print_prefix += "{}:".format(LEVELS[verbosity]["display"])

        def wrapped(text: str) -> None:
            print(print_prefix + text + print_postfix, end = '')

        return LogFunction(wrapped)

    def _init_logger(self) -> None:
        '''Initialise internal logger'''
        debug_fn = self._create_log_function(verbosity = LEVEL_DEBUG)
        verbose_fn = self._create_log_function(verbosity = LEVEL_VERBOSE)
        info_fn = self._create_log_function(verbosity = LEVEL_INFO)
        warn_fn = self._create_log_function(verbosity = LEVEL_WARN)
        error_fn = self._create_log_function(verbosity = LEVEL_ERROR)
        self._logger = Logger(debug_fn, verbose_fn, info_fn, warn_fn, error_fn)

    def log(self) -> Logger:
        '''Yield internal logger'''
        if not hasattr(self, "_logger"):
            self._init_logger()

        return self._logger

    def set_as_global_logger(self) -> None:
        '''Sets global logger to internal logger'''
        if not hasattr(self, "_logger"):
            self._init_logger()

        global global_logger
        global_logger = self._logger

    def override_log(self, **options) -> Logger:
        '''Create custom Logger

        options contains dictionaries for overriding the configured logging
        behaviour. See _create_log_function for informationon how these
        dictionaries should be structured.

        NOTE: these parameters are not checked or sanitised.

        Parameters for options:
        - debug   : dict
        - verbose : dict
        - info    : dict
        - warn    : dict
        - error   : dict
        '''
        if not hasattr(self, "_logger"):
            self._init_logger()

        result = Logger(*astuple(self._logger))

        debug_dict = options.get("debug")
        if debug_dict is not None:
            result.debug = self._create_log_function(**debug_dict)

        verbose_dict = options.get("verbose")
        if verbose_dict is not None:
            result.verbose = self._create_log_function(**verbose_dict)

        info_dict = options.get("info")
        if info_dict is not None:
            result.info = self._create_log_function(**info_dict)

        warn_dict = options.get("warn")
        if warn_dict is not None:
            result.warn = self._create_log_function(**warn_dict)

        error_dict = options.get("error")
        if error_dict is not None:
            result.error = self._create_log_function(**error_dict)

        return result
