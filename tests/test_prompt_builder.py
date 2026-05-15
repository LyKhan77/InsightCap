from __future__ import annotations

import unittest

from backend.core.prompt.builder import PromptBuilder


class PromptBuilderTest(unittest.TestCase):
    def test_live_segment_prompt_includes_previous_segment_caption(self):
        builder = PromptBuilder(frame_prompt="Only report visible activity.")

        prompt = builder.build_live_segment_prompt(
            previous_captions=["Segment 1: a person entered the lobby."],
            segment_num=2,
            source_label="Front Door",
            sampled_frame_count=10,
        )

        self.assertIn("Source: Front Door", prompt)
        self.assertIn("Analyze these 10 live camera frames as one temporal segment", prompt)
        self.assertIn("Segment 1: a person entered the lobby.", prompt)
        self.assertIn("Only report visible activity.", prompt)

    def test_video_segment_prompt_includes_previous_segment_caption(self):
        builder = PromptBuilder(frame_prompt="Only report visible activity.")

        prompt = builder.build_video_segment_prompt(
            previous_captions=["Segment 1: a person entered the lobby."],
            segment_num=2,
            sampled_frame_count=7,
        )

        self.assertIn("Analyze these 7 sampled video frames as one temporal segment", prompt)
        self.assertIn("Segment 1: a person entered the lobby.", prompt)
        self.assertIn("Only report visible activity.", prompt)


if __name__ == "__main__":
    unittest.main()
