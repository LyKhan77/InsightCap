import { expect, test, type Page } from "@playwright/test";

const API_BASE_URL = "http://127.0.0.1:6060";

async function mockVideoAnalysis(page: Page) {
  await page.route(`${API_BASE_URL}/api/v1/analyze/stream`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: [
        'event: init\ndata: {"total_frames":2,"video_fps":30,"duration_seconds":4.8}\n\n',
        'event: frame\ndata: {"index":0,"caption":"A person enters the monitored area.","timestamp_seconds":0}\n\n',
        'event: frame\ndata: {"index":1,"caption":"The person leaves the primary area.","timestamp_seconds":1}\n\n',
        'event: summary\ndata: {"caption":"The uploaded video shows one primary subject moving through a stable scene."}\n\n',
        'event: done\ndata: {"frame_count":2,"duration_seconds":4.8,"device_used":"cuda","model_id":"qwen3.5:0.8b","video_fps":30,"frame_interval":30}\n\n',
      ].join(""),
    });
  });
}

async function mockRtspBackend(page: Page) {
  await page.route(`${API_BASE_URL}/api/v1/rtsp/sessions`, async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: "session-1",
        session_name: "front-gate",
        status: "running",
        source: "rtsp://camera.local/live",
        model_id: "qwen3.5:0.8b",
        sample_every_seconds: 1,
        started_at: "2026-05-13T00:00:00+00:00",
        last_event_at: null,
        last_caption: null,
        captions_emitted: 0,
        reconnect_count: 0,
        lag_ms: null,
        last_error: null,
        auto_label: {
          status: "idle",
          dataset_path: null,
          latest_overlay_path: null,
          frames_labelled: 0,
          frames_dropped: 0,
          chunks_enqueued: 0,
          remaining_seconds: null,
          last_error: null,
        },
      }),
    });
  });

  await page.route(`${API_BASE_URL}/api/v1/rtsp/sessions/session-1`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: "session-1",
        session_name: "front-gate",
        status: "stopped",
        source: "rtsp://camera.local/live",
        model_id: "qwen3.5:0.8b",
        sample_every_seconds: 1,
        started_at: "2026-05-13T00:00:00+00:00",
        last_event_at: "2026-05-13T00:00:01+00:00",
        last_caption: "A person crosses the monitored area from left to right.",
        captions_emitted: 1,
        reconnect_count: 0,
        lag_ms: 118,
        last_error: null,
        auto_label: {
          status: "done",
          dataset_path: "datasets/auto-label/rtsp/session-1",
          latest_overlay_path: null,
          frames_labelled: 10,
          frames_dropped: 0,
          chunks_enqueued: 1,
          remaining_seconds: null,
          last_error: null,
        },
      }),
    });
  });

  await page.route(`${API_BASE_URL}/api/v1/rtsp/sessions/session-1/preview.mjpeg`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/jpeg",
      body: Buffer.from(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Al//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z",
        "base64",
      ),
    });
  });

  await page.routeWebSocket(`${API_BASE_URL.replace("http", "ws")}/api/v1/rtsp/sessions/session-1/events`, (ws) => {
    ws.send(
      JSON.stringify({
        event: "connected",
        session_id: "session-1",
        emitted_at: "2026-05-13T00:00:00+00:00",
        data: { source: "rtsp://camera.local/live", width: 1280, height: 720, fps: 25 },
      }),
    );
    ws.send(
      JSON.stringify({
        event: "caption",
        session_id: "session-1",
        emitted_at: "2026-05-13T00:00:01+00:00",
        data: {
          seq: 1,
          caption: "A person crosses the monitored area from left to right.",
          sampled_frame_count: 10,
          frame_seq_start: 1,
          frame_seq_end: 10,
          captured_at: "2026-05-13T00:00:00+00:00",
          processed_at: "2026-05-13T00:00:01+00:00",
          lag_ms: 118,
        },
      }),
    );
  });
}

test("root page shows mode switch with video and rtsp cards", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Dashboard Live Captioning System")).toBeVisible();
  await expect(page.getByText("Select a monitoring mode")).toBeVisible();
  await expect(page.getByRole("button", { name: /Enter Video/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Enter RTSP/i })).toBeVisible();
});

test("video flow navigates from mode switch, streams captions and export", async ({ page }) => {
  await mockVideoAnalysis(page);
  await page.goto("/");

  // Navigate to video mode
  await page.getByRole("button", { name: /Enter Video/i }).click();
  await expect(page).toHaveURL("/video");
  await expect(page.getByText("Video Mode")).toBeVisible();
  await expect(page.getByText("Live stream")).toBeVisible();

  // Open drawer
  await page.getByLabel("Open controls").click();
  await expect(page.getByText("Video Controls")).toBeVisible();

  // Upload video
  await page.getByLabel("Upload video").setInputFiles({
    name: "demo.mp4",
    mimeType: "video/mp4",
    buffer: Buffer.from("dummy video bytes"),
  });

  await expect(page.getByText("demo.mp4").first()).toBeVisible();
  await expect(page.getByText("Auto-Labelling").first()).toBeVisible();
  await page.getByLabel("Enable").check();
  await expect(page.getByLabel("Auto-label duration minutes")).toBeVisible();

  // Start analysis
  await page.getByRole("button", { name: /Initiate analysis/i }).click();

  await expect(page.getByText(/A person enters the monitored area/i)).toBeVisible({ timeout: 5_000 });
  await expect(page.getByText(/The uploaded video shows one primary subject/i)).toBeVisible({
    timeout: 8_000,
  });
  await expect(page.getByRole("button", { name: /JSON/i })).toBeVisible();
  await expect(page.getByText("Frames", { exact: true })).toBeVisible();
});

test("rtsp flow starts and stops a local monitoring session", async ({ page }) => {
  await mockRtspBackend(page);
  await page.goto("/");

  // Navigate to RTSP mode
  await page.getByRole("button", { name: /Enter RTSP/i }).click();
  await expect(page).toHaveURL("/rtsp");
  await expect(page.getByText("RTSP Mode")).toBeVisible();

  // Open drawer
  await page.getByLabel("Open controls").click();
  await expect(page.getByText("RTSP Controls")).toBeVisible();

  // Fill RTSP fields
  await page.getByLabel("RTSP URL").fill("rtsp://camera.local/live");
  await page.getByLabel("Session name").fill("front-gate");
  await expect(page.getByText("Auto-Labelling").first()).toBeVisible();
  await page.getByLabel("Enable").check();
  await expect(page.getByLabel("Auto-label detector model")).toBeVisible();

  // Start monitoring
  await page.getByRole("button", { name: /Start monitoring/i }).click();

  await expect(page.getByText(/camera online/i)).toBeVisible({ timeout: 5_000 });
  await expect(page.getByText(/Camera connected/i)).toBeVisible();
  await expect(page.getByAltText("RTSP live preview")).toBeVisible();
  await expect(page.getByText(/A person crosses the monitored area/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /Stop monitoring/i })).toBeVisible();

  // Stop monitoring
  await page.getByRole("button", { name: /Stop monitoring/i }).click();
  await expect(page.getByText(/RTSP session stopped/i)).toBeVisible();
});

test("theme toggle switches to dark mode and persists after reload", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /Switch to dark theme/i }).click();
  await expect(page.locator("main")).toHaveAttribute("data-theme", "dark");

  await page.reload();
  await expect(page.locator("main")).toHaveAttribute("data-theme", "dark");

  await page.getByRole("button", { name: /Switch to light theme/i }).click();
  await expect(page.locator("main")).toHaveAttribute("data-theme", "light");
});

test("back button returns to mode switch page", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /Enter Video/i }).click();
  await expect(page).toHaveURL("/video");

  await page.getByRole("button", { name: /Change Mode/i }).click();
  await expect(page).toHaveURL("/");
  await expect(page.getByText("Select a monitoring mode")).toBeVisible();
});

test("main surfaces stay usable across target viewport widths", async ({ page }) => {
  for (const width of [375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.getByText("Dashboard Live Captioning System")).toBeVisible();

    await page.getByRole("button", { name: /Enter Video/i }).click();
    await expect(page.getByText("Live stream")).toBeVisible();

    await page.goBack();
    await page.getByRole("button", { name: /Enter RTSP/i }).click();
    await expect(page.getByText("Live stream")).toBeVisible();
  }
});
