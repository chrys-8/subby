import unittest
import sys

sys.path.append("./src/")

from argparser import SUBCMD_INPUT_SINGLE, CommandLineArgumentError,\
        CommandParser, FlagGroup, Subcommand, Flag, ARG_ENABLE
from cli import parse_cli, CommandLineError, CommandLine
from logger import LEVEL_DEBUG
from srt import DecodeException, SRTDecoder
from stime import Time
from filerange import filerange

TEST_SRT = "test/test.srt"

TEST_SRT_DATA = [
        {
            'duration': {
                'begin': (0, 0, 0, 0),
                'delay_begin': (0, 0, 15, 0),
                'end': (0, 0, 10, 0),
                'delay_end': (0, 0, 25, 0) },
            'content': ["Line 1"] },
        {
            'duration': {
                'begin': (0, 0, 20, 0),
                'delay_begin': (0, 0, 35, 0),
                'end': (0, 0, 25, 0),
                'delay_end': (0, 0, 40, 0) },
            'content': ["Line 2"] },
        {
            'duration': {
                'begin': (0, 0, 59, 0),
                'delay_begin': (0, 1, 14, 0),
                'end': (0, 1, 0, 0),
                'delay_end': (0, 1, 15, 0) },
            'content': ["Line 3"] },
        {
            'duration': {
                'begin': (0, 59, 50, 0),
                'delay_begin': (1, 0, 5, 0),
                'end': (1, 5, 0, 0),
                'delay_end': (1, 5, 15, 0) },
            'content': ["Line 4", "Second line in 4"] }
        ]

TEST_DELAY = 15000

TEST_BOM_SRT = "test/test_bom.srt"
TEST_MISSING_EOF = "test/test_missing_end_blank.srt"
TEST_ICB = "test/test_icb.srt"

TEST_CLI = Subcommand(
    name = "delay",
    function = lambda _: None,
    helpstring = "",
    args = [
        Flag(
            name = "-unit",
            shorthand = "-u",
            choices = ("millisecond", "second", "minute", "ms", "s"),
            default = "ms"),
        Flag(
            name = "-exclusive",
            shorthand = "-x",
            type = ARG_ENABLE),
        Flag(
            name = "delay",
            value_type = int)
        ]
    )

TEST_CLI_2 = [
    TEST_CLI,
    Subcommand(
    name = "dummy",
    function = lambda _: None,
    helpstring = "",
    args = [
        Flag(
            name = "x",
            default = "default"),
        FlagGroup(
            arguments = [
                Flag(name = "-a", type = ARG_ENABLE),
                Flag(name = "-b", type = ARG_ENABLE)
                ],
            mutually_exclusive = True)
        ])
    ]

TEST_CLI_3 = [
        Subcommand(
            name = "dummy_file",
            helpstring = "",
            args = [
                SUBCMD_INPUT_SINGLE
                ]
            )
        ]

class SubtitleFileTestCase(unittest.TestCase):

    def convertDurationtoTimeTuple(self, duration):
        begin = Time.convertValueToTime(duration.begin.value)
        end = Time.convertValueToTime(duration.end.value)
        return begin, end

    def test_decode_SRTFile(self):
        subs = SRTDecoder(filerange(TEST_SRT)).decode()

        self.assertEqual(len(subs.sublines), 4)
        for line, tline in zip(subs.sublines, TEST_SRT_DATA):
            self.assertEqual(len(line.content), len(tline['content']))
            for cline, tcline in zip(line.content, tline['content']):
                self.assertEqual(cline, tcline)

            begin, end = self.convertDurationtoTimeTuple(line.duration)

            self.assertEqual(begin, tline['duration']['begin'])
            self.assertEqual(end, tline['duration']['end'])

    def test_add_delay(self):
        subs = SRTDecoder(filerange(TEST_SRT)).decode()
        for line in subs.sublines:
            line.duration.add_delay(TEST_DELAY)

        for line, tline in zip(subs.sublines, TEST_SRT_DATA):
            begin, end = self.convertDurationtoTimeTuple(line.duration)

            self.assertEqual(begin, tline['duration']['delay_begin'])
            self.assertEqual(end, tline['duration']['delay_end'])

    def test_remove_byte_order_mark(self):
        decoder = SRTDecoder(filerange(TEST_BOM_SRT))
        decoder.read_file()

        line = decoder.filebuffer[0]
        self.assertEqual(line.startswith("\xEF\xBB\xBF"), False)

        file = decoder.decode()
        self.assertEqual(len(file.sublines), 1)

        decoder.cleanup()

    def test_missing_blank_line_end_of_file(self):
        decoder = SRTDecoder(filerange(TEST_MISSING_EOF))

        file = decoder.decode()
        self.assertEqual(len(file.sublines), 4)

        stats = decoder.stats
        self.assertEqual(stats.missing_end_blank_line, True)

        decoder_normal = SRTDecoder(filerange(TEST_SRT))
        decoder_normal.decode()
        self.assertEqual(decoder_normal.stats.missing_end_blank_line, False)

    def test_detect_non_unicode_encoding(self):
        try:
            decoder = SRTDecoder(filerange(TEST_ICB))
            decoder.decode()
            self.assertEqual(decoder.encoding, "latin-1")

        except DecodeException:
            self.fail("Test file is not decoded correctly")

class CommandLineTestCase(unittest.TestCase):

    def test_missing_positional_argument(self):
        parser = CommandParser([TEST_CLI])
        with self.assertRaises(CommandLineArgumentError):
            parser.parse_args_2(["-q", "delay", "-unit:ms"])

    def test_missing_with_defaults(self):
        parser = CommandParser(TEST_CLI_2)
        args = parser.parse_args_2(["dummy"])
        self.assertIsNotNone(args)
        if args is None:
            self.fail()
        self.assertIn("x", args)
        self.assertEqual(args["x"], "default")

    def test_valid_arguments(self):
        parser = CommandParser([TEST_CLI])
        args = parser.parse_args_2(
                ["-q", "delay", "-unit:s", "120", "-exclusive"])
        self.assertIsNotNone(args)
        if args is None:
            self.fail()
        self.assertIn("quiet", args)
        self.assertTrue(args["quiet"])
        self.assertIn("subcmd", args)
        self.assertEqual(args["subcmd"], "delay")
        self.assertIn("unit", args)
        self.assertEqual(args["unit"], "s")
        self.assertIn("delay", args)
        self.assertEqual(args["delay"], 120)
        self.assertIn("exclusive", args)
        self.assertTrue(args["exclusive"])

    def test_invalid_input_type_conversion(self):
        parser = CommandParser([TEST_CLI])
        with self.assertRaises(CommandLineArgumentError):
            parser.parse_args_2(["delay", "two"])

    def test_argument_defaults(self):
        parser = CommandParser([TEST_CLI])
        args = parser.parse_args_2(["delay", "100"])
        self.assertIsNotNone(args)
        if args is None:
            self.fail()
        self.assertIn("unit", args)
        self.assertEqual(args["unit"], "ms")
        self.assertIn("exclusive", args)
        self.assertEqual(args["exclusive"], False)

    def test_disallow_multi_command(self):
        parser = CommandParser(TEST_CLI_2)
        with self.assertRaises(CommandLineArgumentError):
            parser.parse_args_2(["delay", "100", "dummy"])

    def test_choice_validation(self):
        parser = CommandParser([TEST_CLI])
        with self.assertRaises(CommandLineArgumentError):
            parser.parse_args_2(["delay", "-unit", "pico", "1"])

    def test_negative_number_argument(self):
        parser = CommandParser([TEST_CLI])
        args = parser.parse_args_2(["delay", "-100"])
        self.assertIsNotNone(args)
        if args is None:
            self.fail()
        self.assertIn("delay", args)
        self.assertEqual(args["delay"], -100)

    def test_mutual_exclusion(self):
        parser = CommandParser(TEST_CLI_2)
        with self.assertRaises(CommandLineArgumentError):
            parser.parse_args_2(["dummy", "-a", "-b"])

    def test_validation(self):
        parser = CommandParser(TEST_CLI_3)
        args = parser.parse_args_2(["-q", "dummy_file", "bad_file.txt"])
        self.assertIsNone(args)

    def test_post_processing(self):
        parser = CommandParser([TEST_CLI])
        args = parser.parse_args_2(["-debug"])
        self.assertIsNotNone(args)
        if args is None:
            self.fail()
        self.assertIn("verbosity", args)
        self.assertEqual(args["verbosity"], LEVEL_DEBUG)

class CommandLineTestCase_2(unittest.TestCase):
    def test_positional_arguments(self):
        test_args: list[str] = ["zero", "one", "two", "three"]
        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert positionals set correctly
        self.assertEqual(len(args.positional_arguments), len(test_args))
        for arg, test_arg in zip(args.positional_arguments, test_args):
            self.assertEqual(arg, test_arg, f"({test_arg} -> {arg})")

        # assert no other field set
        self.assertEqual(len(args.named_arguments.values()), 0)
        self.assertEqual(len(args.flags.values()), 0)

    def do_list_test(self, test_args: list[str]) -> None:
        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert flags set correctly
        for test_flag in test_args:
            flag = args.flags.get(test_flag)
            self.assertIsNotNone(flag, f"({test_flag})")
            self.assertTrue(flag, f"({test_flag})")

        # assert not other field set
        self.assertEqual(len(args.positional_arguments), 0)
        self.assertEqual(len(args.named_arguments.values()), 0)

    def test_flag_argument(self):
        test_args: list[str] = ["--no-list", "--quiet", "--empty"]
        self.do_list_test(test_args)

    def test_named_argument(self):
        test_args_dict: dict[str, str] = {
                "--value-0": "zero",
                "--value-1": "one",
                "--value-2": "two" }

        test_args: list[str] = []
        for key, value in test_args_dict.items():
            test_args.append(key)
            test_args.append(value)

        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert named arguments set correctly
        for key, values in args.named_arguments.items():
            self.assertIn(key, test_args_dict.keys(), f"({key})")
            test_value = test_args_dict.get(key)
            self.assertEqual(len(values), 1, f"({key})")
            self.assertEqual(values[0], test_value, f"({key})")

        # assert no other fields set
        self.assertEqual(len(args.positional_arguments), 0)
        self.assertEqual(len(args.flags.values()), 0)

    def test_multiple_arguments(self):
        test_args_dict: dict[str, tuple[tuple[str, ...], str]] = {
                "--one": (("one", "two", "three"), ":,"),
                "--two": (("one", "two"), ":;"),
                "--three": (("a", "b"), "=,"),
                "--four": (("one", "two", "three"), "=;")}

        test_args: list[str] = [
                "{}{}{}".format(
                    key,
                    value[1][0],
                    "{}".format(value[1][1]).join(value[0]))
                for key, value in test_args_dict.items()]

        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert named arguments set correctly
        for test_name, test_data in test_args_dict.items():
            test_values, _ = test_data
            self.assertIn(test_name, args.named_arguments)
            values = args.named_arguments[test_name]
            self.assertSequenceEqual(test_values, values, f"({test_name})")

        # assert no other field set
        self.assertEqual(len(args.positional_arguments), 0)
        self.assertEqual(len(args.flags.values()), 0)

    def test_mismatched_list_separators(self):
        test_args: list[str] = ["--list:a,b;c"]
        with self.assertRaises(CommandLineError):
            parse_cli(test_args)

    def test_shorthand_flag(self):
        test_args: list[str] = ["-u", "-a", "-b", "-F"]
        self.do_list_test(test_args)

    def test_shorthand_argument_explicit_value(self):
        test_name = "-C"
        test_value = "hello"
        test_args: list[str] = [f"{test_name}{test_value}"]
        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert named argument is set correctly
        self.assertIn(test_name, args.named_arguments)
        value = args.named_arguments[test_name][0]
        self.assertEqual(value, test_value)

        # assert no other field is set
        self.assertEqual(len(args.positional_arguments), 0)
        self.assertEqual(len(args.flags.values()), 0)

    def test_shorthand_argument_list(self):
        test_args_dict: dict[str, tuple[tuple[str, ...], str]] = {
                "-o": (("one", "two", "three"), ":,"),
                "-t": (("one", "two"), ":;"),
                "-x": (("a", "b"), "=,"),
                "-f": (("one", "two", "three"), "=;")}

        test_args: list[str] = [
                "{}{}{}".format(
                    key,
                    value[1][0],
                    "{}".format(value[1][1]).join(value[0]))
                for key, value in test_args_dict.items()]

        try:
            args = parse_cli(test_args)
        except CommandLineError as err:
            self.fail(err)

        self.assertIsInstance(args, CommandLine)

        # assert named arguments set correctly
        for test_name, test_data in test_args_dict.items():
            test_values, _ = test_data
            self.assertIn(test_name, args.named_arguments)
            values = args.named_arguments[test_name]
            self.assertSequenceEqual(test_values, values, f"({test_name})")

        # assert no other field set
        self.assertEqual(len(args.positional_arguments), 0)
        self.assertEqual(len(args.flags.values()), 0)

if __name__ == "__main__":
    unittest.main()
