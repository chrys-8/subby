from dataclasses import dataclass

class CommandLineError(Exception):
    pass

@dataclass()
class CommandLine:
    positional_arguments: tuple[str, ...]
    named_arguments: dict[str, tuple[str, ...]]
    flags: dict[str, bool]

def parse_cli(args: list[str]) -> CommandLine:
    raise NotImplementedError
