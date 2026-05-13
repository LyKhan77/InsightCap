import { expect, test } from "@playwright/test";

test("root page shows mode switch with video and rtsp cards", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Dashboard Live Captioning System")).toBeVisible();
  await expect(page.getByText("Select a monitoring mode")).toBeVisible();
  await expect(page.getByRole("button", { name: /Enter Video/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Enter RTSP/i })).toBeVisible();
});

test("video flow navigates from mode switch, simulates captions and export", async ({ page }) => {
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

  // Start analysis
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

  // Start monitoring
  await page.getByRole("button", { name: /Start monitoring/i }).click();

  await expect(page.getByText(/camera online/i)).toBeVisible({ timeout: 5_000 });
  await expect(page.getByText(/Camera connected/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /Stop monitoring/i })).toBeVisible();

  // Stop monitoring
  await page.getByRole("button", { name: /Stop monitoring/i }).click();
  await expect(page.getByText(/RTSP session stopped locally/i)).toBeVisible();
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

  await page.getByRole("button", { name: /Back/i }).click();
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
