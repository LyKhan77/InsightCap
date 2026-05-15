import { analyzeStreamUrl } from "./api";

export type VideoStreamEvent =
  | {
      event: "init";
      data: {
        total_frames: number;
        video_fps: number;
        duration_seconds: number;
      };
    }
  | {
      event: "frame";
      data: {
        index: number;
        caption: string;
        timestamp_seconds: number;
        timestamp_end_seconds?: number;
        sampled_frame_count?: number | null;
        frame_index_start?: number;
        frame_index_end?: number;
      };
    }
  | {
      event: "summary";
      data: {
        caption: string;
      };
    }
  | {
      event: "done";
      data: {
        frame_count: number;
        duration_seconds: number;
        device_used: string;
        model_id: string;
        video_fps?: number;
        frame_interval?: number;
      };
    };

type StreamAnalysisInput = {
  file: File;
  model: string;
  framePrompt?: string;
  summaryPrompt?: string;
  signal?: AbortSignal;
  onEvent: (event: VideoStreamEvent) => void;
};

export async function streamVideoAnalysis(input: StreamAnalysisInput) {
  const formData = new FormData();
  formData.append("file", input.file);
  formData.append("model", input.model);
  if (input.framePrompt) formData.append("frame_prompt", input.framePrompt);
  if (input.summaryPrompt) formData.append("summary_prompt", input.summaryPrompt);

  const response = await fetch(analyzeStreamUrl(), {
    method: "POST",
    body: formData,
    signal: input.signal,
  });

  if (!response.ok) {
    throw new Error(await readStreamError(response));
  }
  if (!response.body) {
    throw new Error("Analysis stream did not return a response body.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split(/\n\n/);
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const parsed = parseSseChunk(chunk);
      if (parsed) input.onEvent(parsed);
    }
  }

  if (buffer.trim()) {
    const parsed = parseSseChunk(buffer);
    if (parsed) input.onEvent(parsed);
  }
}

function parseSseChunk(chunk: string): VideoStreamEvent | null {
  let eventName = "";
  const dataLines: string[] = [];

  for (const line of chunk.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (!eventName || dataLines.length === 0) return null;

  return {
    event: eventName,
    data: JSON.parse(dataLines.join("\n")),
  } as VideoStreamEvent;
}

async function readStreamError(response: Response) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return `${response.status} ${response.statusText}`.trim();
  }
}
