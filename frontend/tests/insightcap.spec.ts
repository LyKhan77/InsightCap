import { expect, test } from "@playwright/test";

test("mode selector renders both production workflows", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: /Video Analysis/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /RTSP Monitoring/i })).toBeVisible();
  await expect(page.getByText(/production-grade interface/i)).toBeVisible();
});

test("video flow simulates captions, summary, metadata, and export", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("mode-video").click();

  await page.getByLabel("Upload video").setInputFiles({
    name: "demo.mp4",
    mimeType: "video/mp4",
    buffer: Buffer.from("dummy video bytes"),
  });

  await expect(page.getByText("demo.mp4").first()).toBeVisible();
  await page.getByRole("button", { name: /Initiate analysis/i }).click();

  await expect(page.getByText(/Streaming sampled frame captions/i)).toBeVisible({
    timeout: 5_000,
  });
  await expect(page.getByText(/The uploaded video shows one primary subject/i)).toBeVisible({
    timeout: 8_000,
  });
  await expect(page.getByRole("button", { name: /JSON/i })).toBeVisible();
  await expect(page.getByText("Frames", { exact: true })).toBeVisible();
});

test("rtsp flow starts and stops a local monitoring session", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("mode-rtsp").click();

  await page.getByLabel("RTSP URL").fill("rtsp://camera.local/live");
  await page.getByLabel("Session name").fill("front-gate");
  await page.getByRole("button", { name: /Start monitoring/i }).click();

  await expect(page.getByText(/camera online/i)).toBeVisible({ timeout: 5_000 });
  await expect(page.getByText(/Camera connected/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /Stop monitoring/i })).toBeVisible();

  await page.getByRole("button", { name: /Stop monitoring/i }).click();
  await expect(page.getByText(/RTSP session stopped locally/i)).toBeVisible();
});

test("main surfaces stay usable across target viewport widths", async ({ page }) => {
  for (const width of [375, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Video Analysis/i })).toBeVisible();
    await page.getByTestId("mode-video").click();
    await expect(page.getByText("Video controls")).toBeVisible();
    await expect(page.getByText("Live stream")).toBeVisible();
  }
});
