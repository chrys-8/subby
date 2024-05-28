import unittest
import sys

sys.path.append("./src/")

from argparser import SUBCMD_INPUT_SINGLE, CommandLineArgumentError,\
        CommandParser, FlagGroup, Subcommand, Flag, ARG_ENABLE
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

if __name__ == "__main__":
    unittest.main()
