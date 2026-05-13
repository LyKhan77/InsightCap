from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend.core.video import live_reader
from backend.core.video.live_reader import LiveStreamReader


class LiveStreamReaderTest(unittest.TestCase):
    def test_rtsp_reader_uses_tcp_ffmpeg_options(self):
        calls = []

        class FakeCapture:
            def __init__(self, *args):
                calls.append(args)

            def isOpened(self):
                return True

            def release(self):
                return None

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)
            with patch.object(live_reader.cv2, "VideoCapture", FakeCapture):
                reader = LiveStreamReader(
                    "rtsp://user:pass@192.168.0.64:554/Streaming/Channels/102",
                    open_timeout_ms=1234,
                    read_timeout_ms=5678,
                )
                reader.open()

                self.assertTrue(calls)
                self.assertEqual(calls[0][1], live_reader.cv2.CAP_FFMPEG)
                self.assertIn(live_reader.cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, calls[0][2])
                self.assertIn(live_reader.cv2.CAP_PROP_READ_TIMEOUT_MSEC, calls[0][2])
                self.assertIn(
                    "rtsp_transport;tcp",
                    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"],
                )


if __name__ == "__main__":
    unittest.main()
