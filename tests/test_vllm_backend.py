from __future__ import annotations

import unittest
import sys
from types import SimpleNamespace

import numpy as np

from backend.core.config import InferenceConfig
from backend.core.inference.factory import get_backend
from backend.core.inference.vllm_backend import VLLMBackend


class FakeCompletions:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.chat = SimpleNamespace(
            completions=FakeCompletions(response)
        )


class FakeOpenAI(FakeClient):
    def __init__(self, **kwargs):
        super().__init__(response_with_text("ok"))
        self.kwargs = kwargs


def response_with_text(text: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text)
            )
        ]
    )


def chunk_with_text(text: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=text)
            )
        ]
    )


class VLLMBackendTest(unittest.TestCase):
    def test_generate_for_frame_sends_openai_image_url_payload(self):
        client = FakeClient(response_with_text("caption"))
        config = InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm", stream=False)
        backend = VLLMBackend(config, client=client)
        frame = np.zeros((8, 8, 3), dtype=np.uint8)

        output = list(backend.generate_for_frame(frame, "Describe this frame."))

        self.assertEqual(output, ["caption"])
        call = client.chat.completions.calls[0]
        self.assertEqual(call["model"], "qwen3.5:0.8b")
        self.assertFalse(call["stream"])
        self.assertEqual(call["temperature"], 0.7)
        self.assertEqual(call["top_p"], 0.8)
        self.assertEqual(call["presence_penalty"], 1.5)
        self.assertEqual(call["extra_body"], {"top_k": 20})
        content = call["messages"][0]["content"]
        self.assertEqual(content[0], {"type": "text", "text": "Describe this frame."})
        self.assertEqual(content[1]["type"], "image_url")
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    def test_generate_for_frames_sends_multi_image_payload(self):
        client = FakeClient(response_with_text("segment caption"))
        config = InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm", stream=False)
        backend = VLLMBackend(config, client=client)
        frames = [np.zeros((8, 8, 3), dtype=np.uint8) for _ in range(10)]

        output = list(backend.generate_for_frames(frames, "Analyze this segment."))

        self.assertEqual(output, ["segment caption"])
        content = client.chat.completions.calls[0]["messages"][0]["content"]
        self.assertEqual(content[0], {"type": "text", "text": "Analyze this segment."})
        image_items = [item for item in content if item["type"] == "image_url"]
        self.assertEqual(len(image_items), 10)
        self.assertTrue(
            all(item["image_url"]["url"].startswith("data:image/jpeg;base64,") for item in image_items)
        )

    def test_streaming_chunks_are_yielded(self):
        client = FakeClient([chunk_with_text("cap"), chunk_with_text("tion")])
        config = InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm", stream=True)
        backend = VLLMBackend(config, client=client)
        frame = np.zeros((8, 8, 3), dtype=np.uint8)

        output = list(backend.generate_for_frame(frame, "Describe this frame."))

        self.assertEqual(output, ["cap", "tion"])
        self.assertTrue(client.chat.completions.calls[0]["stream"])

    def test_summarize_uses_text_only_message(self):
        client = FakeClient(response_with_text("summary"))
        config = InferenceConfig(model_id="qwen3.5:0.8b", backend="vllm", stream=False)
        backend = VLLMBackend(config, client=client)

        output = list(backend.summarize(["Frame one."], "Summarize."))

        self.assertEqual(output, ["summary"])
        content = client.chat.completions.calls[0]["messages"][0]["content"]
        self.assertIn("Frame 1: Frame one.", content)

    def test_factory_returns_vllm_backend_by_default(self):
        original_openai = sys.modules.get("openai")
        sys.modules["openai"] = SimpleNamespace(OpenAI=FakeOpenAI)
        try:
            backend = get_backend(InferenceConfig(backend="vllm"))
        finally:
            if original_openai is None:
                sys.modules.pop("openai", None)
            else:
                sys.modules["openai"] = original_openai

        self.assertIsInstance(backend, VLLMBackend)

    def test_factory_rejects_unknown_backend(self):
        with self.assertRaisesRegex(ValueError, "Unknown backend"):
            get_backend(InferenceConfig(backend="missing"))


if __name__ == "__main__":
    unittest.main()
