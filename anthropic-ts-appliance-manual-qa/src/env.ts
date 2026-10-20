// Loads the repo-root .env (if present) so ANTHROPIC_API_KEY is available.
import { existsSync } from "node:fs";
import { resolve } from "node:path";

for (const p of [resolve(process.cwd(), ".env"), resolve(process.cwd(), "../.env")]) {
  if (existsSync(p)) {
    process.loadEnvFile(p);
    break;
  }
}

// Opik reads these at first use: local self-hosted backend, default workspace, and the project
// every trace lands in. Set before anything imports "opik".
process.env.OPIK_URL_OVERRIDE ??= "http://localhost:5173/api/";
process.env.OPIK_WORKSPACE ??= "default";
process.env.OPIK_PROJECT_NAME ??= "anthropic-ts-appliance-manual-qa";
