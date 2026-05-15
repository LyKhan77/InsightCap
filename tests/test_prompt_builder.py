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

    def test_short_video_prompt_mentions_single_segment_analysis(self):
        builder = PromptBuilder(frame_prompt="Keep it factual.")

        prompt = builder.build_short_video_prompt(sampled_frame_count=3)

        self.assertIn("Analyze these 3 sampled video frames as one short video segment", prompt)
        self.assertIn("Describe the most meaningful activity across the full clip", prompt)
        self.assertIn("Keep it factual.", prompt)


if __name__ == "__main__":
    unittest.main()
