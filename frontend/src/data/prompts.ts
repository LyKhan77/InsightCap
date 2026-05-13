export type VideoPromptPreset = {
  framePrompt: string;
  summaryPrompt: string;
};

export type RtspPromptPreset = {
  framePrompt: string;
};

export const VIDEO_PROMPT_PRESETS: Record<string, VideoPromptPreset> = {
  default: {
    framePrompt:
      "Describe what is happening in this video frame. Be concise, factual, and specific. Only describe what is clearly visible.",
    summaryPrompt:
      "You are given frame-by-frame descriptions from a video.\nIf the request below is a question, answer it directly and precisely.\nIf the request asks for a summary, write a coherent narrative.\nBe factual and avoid guessing anything not described.",
  },
  detailed: {
    framePrompt:
      "Provide a detailed description of this video frame.\nInclude: subjects, objects, actions, setting, lighting, colors, and any visible text.\nFor colors, be precise (e.g., white, black, silver, gray, red, blue).\nNote: silver and gray are NOT white. Be thorough.",
    summaryPrompt:
      "You are given detailed frame-by-frame descriptions from a video.\nWrite a comprehensive summary (3-5 sentences) covering:\n- Main events and their sequence\n- Key subjects and their attributes\n- Context and setting\nBe specific and factual.",
  },
  concise: {
    framePrompt:
      "Briefly describe this frame in one sentence. Focus only on the main subject and action.",
    summaryPrompt:
      "Summarize the video in one sentence. Capture the main subject and key action only.",
  },
  narrative: {
    framePrompt:
      "Describe this frame as part of an ongoing story. Focus on the narrative flow: who is doing what, and why. Maintain continuity with previous events.",
    summaryPrompt:
      "You have frame descriptions from a video. Tell the story of what happened from beginning to end. Use a flowing narrative style (2-3 paragraphs).",
  },
  analytical: {
    framePrompt:
      "Analyze this frame and identify all visible entities.\nFor each entity, report:\n- Type (person, vehicle, object, animal)\n- Color (be precise: white, black, silver, gray, red, blue, etc.)\nNote: silver/gray are NOT white.\n- Position (left, center, right, foreground, background)\n- Action (standing, moving, passing, etc.)\nBe factual and precise.",
    summaryPrompt:
      "Based on the frame descriptions, provide a structured summary:\n1. Total count of each entity type\n2. Colors observed (only report colors you are confident about)\n3. Key actions and events\nBe factual and precise with counts.",
  },
  traffic: {
    framePrompt:
      "Analyze this traffic camera frame. For each vehicle, report:\n- Type (car, truck, SUV, motorcycle, bus, bicycle)\n- Color (be precise: white, black, silver, gray, red, blue, etc.)\nWARNING: silver/gray vehicles are NOT white. Distinguish them carefully.\n- Lane position (left, center, right)\n- Direction (approaching, departing, passing through)\nBe factual and precise with colors.",
    summaryPrompt:
      "Based on the frame descriptions, answer:\n1. Total number of vehicles\n2. Count by type (car, truck, SUV, etc.)\n3. Count by color (distinguish white from silver/gray)\n4. Traffic flow observations\nBe precise with counts and color distinctions.",
  },
};

export const RTSP_PROMPT_PRESETS: Record<string, RtspPromptPreset> = {
  default: {
    framePrompt:
      "Describe what is happening in this frame. Be concise and factual. Only describe what is clearly visible.",
  },
  security: {
    framePrompt:
      "Security monitoring frame analysis:\n- People: count, location, behavior (normal/suspicious)\n- Vehicles: if present, note type and color\n  (white, black, silver, gray - silver is NOT white)\n- Objects: any unattended items\n- Exits/entrances: any activity\nReport anomalies immediately. Be brief and factual.",
  },
  activity: {
    framePrompt:
      "Human activity analysis:\n- People count\n- Actions (walking, running, standing, interacting)\n- Clothing colors (be precise: white, black, etc.)\n- Movement direction\nBe concise and factual.",
  },
  traffic: {
    framePrompt:
      "Analyze this traffic camera frame. For each vehicle, report:\n- Type: car, truck, SUV, motorcycle, bus\n- Color: white, black, silver, gray, red, blue, etc.\n  WARNING: silver/gray are NOT white. Be precise.\n- Lane: left, center, right\n- Movement: approaching, departing, passing\nBe precise with color identification.",
  },
};
