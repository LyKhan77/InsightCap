from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from backend.app.schemas.rtsp import RTSPSessionCreateRequest
from backend.app.services.rtsp.session import RtspSession
from backend.app.services.rtsp.utils import _mask_error_message, _mask_rtsp_url


class FakeSegmentBackend:
    def __init__(self):
        self.calls = []

    def generate_for_frame(self, frame, prompt):
        yield "unused"

    def generate_for_frames(self, frames, prompt):
        self.calls.append((frames, prompt))
        yield f"segment {len(self.calls)}"


class RtspServiceTest(unittest.TestCase):
    def test_rtsp_error_message_masks_credentials(self):
        raw = "rtsp://admin:secret@192.168.0.64:554/Streaming/Channels/102"
        masked = _mask_rtsp_url(raw)

        message = f"Cannot open live stream: {raw}"

        self.assertEqual(
            _mask_error_message(message, raw, masked),
            "Cannot open live stream: rtsp://***@192.168.0.64:554/Streaming/Channels/102",
        )

    def test_rtsp_segment_buffer_emits_only_after_ten_sampled_frames(self):
        backend = FakeSegmentBackend()
        request = RTSPSessionCreateRequest(
            rtsp_url="rtsp://admin:secret@192.168.0.64/stream",
            session_name="Door",
        )
        with patch("backend.app.services.rtsp.session.get_backend", return_value=backend):
            session = RtspSession("session-1", request)

        emitted = []
        with patch.object(session, "_emit", side_effect=lambda event, **data: emitted.append((event, data))):
            for frame_seq in range(1, 10):
                frame = np.full((4, 4, 3), frame_seq, dtype=np.uint8)
                session._process_sampled_live_frame(frame_seq, frame)

            self.assertEqual(emitted, [])
            self.assertEqual(backend.calls, [])

            session._process_sampled_live_frame(10, np.full((4, 4, 3), 10, dtype=np.uint8))

        self.assertEqual(len(emitted), 1)
        event, data = emitted[0]
        self.assertEqual(event, "caption")
        self.assertEqual(data["seq"], 1)
        self.assertEqual(data["caption"], "segment 1")
        self.assertEqual(data["sampled_frame_count"], 10)
        self.assertEqual(data["frame_seq_start"], 1)
        self.assertEqual(data["frame_seq_end"], 10)
        self.assertEqual(len(backend.calls[0][0]), 10)

    def test_rtsp_segment_prompt_uses_previous_segment_caption(self):
        backend = FakeSegmentBackend()
        request = RTSPSessionCreateRequest(
            rtsp_url="rtsp://admin:secret@192.168.0.64/stream",
            session_name="Door",
        )
        with patch("backend.app.services.rtsp.session.get_backend", return_value=backend):
            session = RtspSession("session-1", request)

        with patch.object(session, "_emit"):
            for frame_seq in range(1, 21):
                frame = np.full((4, 4, 3), frame_seq, dtype=np.uint8)
                session._process_sampled_live_frame(frame_seq, frame)

        self.assertEqual(len(backend.calls), 2)
        second_prompt = backend.calls[1][1]
        self.assertIn("segment 1", second_prompt)
        self.assertNotIn("unused", second_prompt)

    def test_rtsp_reset_clears_partial_segment_buffer(self):
        backend = FakeSegmentBackend()
        request = RTSPSessionCreateRequest(
            rtsp_url="rtsp://admin:secret@192.168.0.64/stream",
            session_name="Door",
        )
        with patch("backend.app.services.rtsp.session.get_backend", return_value=backend):
            session = RtspSession("session-1", request)

        for frame_seq in range(1, 6):
            frame = np.full((4, 4, 3), frame_seq, dtype=np.uint8)
            session._process_sampled_live_frame(frame_seq, frame)

        session._reset_live_buffers()

        with patch.object(session, "_emit") as emit:
            for frame_seq in range(6, 15):
                frame = np.full((4, 4, 3), frame_seq, dtype=np.uint8)
                session._process_sampled_live_frame(frame_seq, frame)

        emit.assert_not_called()
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
