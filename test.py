import unittest
import sys
sys.path.append("./src/")

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


if __name__ == "__main__":
    unittest.main()
