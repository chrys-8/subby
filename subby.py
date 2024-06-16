# extend import paths
import sys
from typing import Any
sys.path.append("./src/")

from cli import CommandLine
from logger import info
from subcommand.display import subcommand_display
from subcommand.delay import subcommand_delay
from subcommand.trim import subcommand_trim

# interactive mode imports
import interactive as imode

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
    parser: CommandLine = CommandLine(config, **program_options)
    args: dict[str, Any] | None = parser.parse_args()

    if args is None:
        # assume error was provided by validators in CommandLine
        return

    if args["subcmd"] is None:
        interactive_mode = imode.InteractiveMode(config, args)
        interactive_mode.start()
        return

    for subcommand in config:
        if args["subcmd"] == subcommand.name:
            subcommand.function(args)

if __name__ == "__main__":
    main()
