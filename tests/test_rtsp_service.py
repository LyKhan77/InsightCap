from __future__ import annotations

import unittest

from backend.app.services.rtsp.utils import _mask_error_message, _mask_rtsp_url


class RtspServiceTest(unittest.TestCase):
    def test_rtsp_error_message_masks_credentials(self):
        raw = "rtsp://admin:secret@192.168.0.64:554/Streaming/Channels/102"
        masked = _mask_rtsp_url(raw)

        message = f"Cannot open live stream: {raw}"

        self.assertEqual(
            _mask_error_message(message, raw, masked),
            "Cannot open live stream: rtsp://***@192.168.0.64:554/Streaming/Channels/102",
        )


if __name__ == "__main__":
    unittest.main()
