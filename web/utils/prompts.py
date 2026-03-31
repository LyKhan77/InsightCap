"""Prompt presets for Video and RTSP modes."""
from __future__ import annotations

VIDEO_PROMPT_PRESETS = {
    "default": {
        "frame_prompt": (
            "Describe what is happening in this video frame. "
            "Be concise, factual, and specific. "
            "Only describe what is clearly visible."
        ),
        "summary_prompt": (
            "You are given frame-by-frame descriptions from a video.\n"
            "If the request below is a question, answer it directly and precisely.\n"
            "If the request asks for a summary, write a coherent narrative.\n"
            "Be factual and avoid guessing anything not described."
        ),
    },
    "detailed": {
        "frame_prompt": (
            "Provide a detailed description of this video frame.\n"
            "Include: subjects, objects, actions, setting, lighting, colors, and any visible text.\n"
            "For colors, be precise (e.g., white, black, silver, gray, red, blue).\n"
            "Note: silver and gray are NOT white. Be thorough."
        ),
        "summary_prompt": (
            "You are given detailed frame-by-frame descriptions from a video.\n"
            "Write a comprehensive summary (3-5 sentences) covering:\n"
            "- Main events and their sequence\n"
            "- Key subjects and their attributes\n"
            "- Context and setting\n"
            "Be specific and factual."
        ),
    },
    "concise": {
        "frame_prompt": (
            "Briefly describe this frame in one sentence. "
            "Focus only on the main subject and action."
        ),
        "summary_prompt": (
            "Summarize the video in one sentence. "
            "Capture the main subject and key action only."
        ),
    },
    "narrative": {
        "frame_prompt": (
            "Describe this frame as part of an ongoing story. "
            "Focus on the narrative flow: who is doing what, and why. "
            "Maintain continuity with previous events."
        ),
        "summary_prompt": (
            "You have frame descriptions from a video. "
            "Tell the story of what happened from beginning to end. "
            "Use a flowing narrative style (2-3 paragraphs)."
        ),
    },
    "analytical": {
        "frame_prompt": (
            "Analyze this frame and identify all visible entities.\n"
            "For each entity, report:\n"
            "- Type (person, vehicle, object, animal)\n"
            "- Color (be precise: white, black, silver, gray, red, blue, etc.)\n"
            "Note: silver/gray are NOT white.\n"
            "- Position (left, center, right, foreground, background)\n"
            "- Action (standing, moving, passing, etc.)\n"
            "Be factual and precise."
        ),
        "summary_prompt": (
            "Based on the frame descriptions, provide a structured summary:\n"
            "1. Total count of each entity type\n"
            "2. Colors observed (only report colors you are confident about)\n"
            "3. Key actions and events\n"
            "Be factual and precise with counts."
        ),
    },
    "traffic": {
        "frame_prompt": (
            "Analyze this traffic camera frame. For each vehicle, report:\n"
            "- Type (car, truck, SUV, motorcycle, bus, bicycle)\n"
            "- Color (be precise: white, black, silver, gray, red, blue, etc.)\n"
            "WARNING: silver/gray vehicles are NOT white. Distinguish them carefully.\n"
            "- Lane position (left, center, right)\n"
            "- Direction (approaching, departing, passing through)\n"
            "Be factual and precise with colors."
        ),
        "summary_prompt": (
            "Based on the frame descriptions, answer:\n"
            "1. Total number of vehicles\n"
            "2. Count by type (car, truck, SUV, etc.)\n"
            "3. Count by color (distinguish white from silver/gray)\n"
            "4. Traffic flow observations\n"
            "Be precise with counts and color distinctions."
        ),
    },
}

RTSP_PROMPT_PRESETS = {
    "default": {
        "frame_prompt": (
            "Describe what is happening in this frame. "
            "Be concise and factual. Only describe what is clearly visible."
        ),
    },
    "security": {
        "frame_prompt": (
            "Security monitoring frame analysis:\n"
            "- People: count, location, behavior (normal/suspicious)\n"
            "- Vehicles: if present, note type and color\n"
            "  (white, black, silver, gray - silver is NOT white)\n"
            "- Objects: any unattended items\n"
            "- Exits/entrances: any activity\n"
            "Report anomalies immediately. Be brief and factual."
        ),
    },
    "activity": {
        "frame_prompt": (
            "Human activity analysis:\n"
            "- People count\n"
            "- Actions (walking, running, standing, interacting)\n"
            "- Clothing colors (be precise: white, black, etc.)\n"
            "- Movement direction\n"
            "Be concise and factual."
        ),
    },
    "traffic": {
        "frame_prompt": (
            "Analyze this traffic camera frame. For each vehicle, report:\n"
            "- Type: car, truck, SUV, motorcycle, bus\n"
            "- Color: white, black, silver, gray, red, blue, etc.\n"
            "  WARNING: silver/gray are NOT white. Be precise.\n"
            "- Lane: left, center, right\n"
            "- Movement: approaching, departing, passing\n"
            "Be precise with color identification."
        ),
    },
}


def get_video_prompts(
    preset: str = "default",
    frame_prompt: str | None = None,
    summary_prompt: str | None = None
) -> tuple[str, str]:
    """Get video mode prompts (frame_prompt, summary_prompt)."""
    base = VIDEO_PROMPT_PRESETS.get(preset, VIDEO_PROMPT_PRESETS["default"])
    return (
        frame_prompt or base["frame_prompt"],
        summary_prompt or base["summary_prompt"],
    )


def get_rtsp_prompts(preset: str = "default", frame_prompt: str | None = None) -> str:
    """Get RTSP mode prompt (frame_prompt only)."""
    base = RTSP_PROMPT_PRESETS.get(preset, RTSP_PROMPT_PRESETS["default"])
    return frame_prompt or base["frame_prompt"]