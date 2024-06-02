# extend import paths
import sys
from typing import Any
sys.path.append("./src/")

from cli import CommandLine
from logger import info
from subcommand.display import subcommand_display
from subcommand.delay import subcommand_delay
from subcommand.trim import subcommand_trim

default_subcommands_configuration = [
        subcommand_display,
        subcommand_delay,
        subcommand_trim
        ]

program_options = {
        "prog_name": "subby",
        "description": "Subtitle Editor"
        }

def main() -> None:
    config = default_subcommands_configuration
<<<<<<< HEAD
    parser: CommandLine = CommandLine(config, **program_options)
    args: dict[str, Any] | None = parser.parse_args()
=======
    args = CommandParser(config).parse_args_2()
>>>>>>> 3c378df0b457217c2bc8c980ec3a0c163a416c48

    if args is None:
        # assume error was provided by validators in CommandLine
        return

    if args["subcmd"] is None:
        info("Interactive mode coming soon! For now, use -h for help.")

    for subcommand in config:
        if args["subcmd"] == subcommand.name:
            if subcommand.function is not None:
                subcommand.function(args)

if __name__ == "__main__":
    main()
