from srt import decodeSRTFile

TEST_FILENAME = "test.srt"
TEST_OUTPUT_FILENAME = "output.srt"

subs = decodeSRTFile(TEST_FILENAME)
subs.filename = TEST_OUTPUT_FILENAME

for subtitle in subs.sublines[4:]:
    subtitle.duration.addDelay(1100)

subs.writeToFile()
