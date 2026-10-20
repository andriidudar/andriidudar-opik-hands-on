// SvelteKit loads this module once when the server starts, so telemetry is
// registered before the first request reaches /api/chat.
import "$lib/server/telemetry";
