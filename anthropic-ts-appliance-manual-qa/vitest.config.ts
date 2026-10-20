import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // The opik SDK's documented off switch: with tracking disabled, tracked functions run as
    // plain functions and nothing is sent to a backend.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
