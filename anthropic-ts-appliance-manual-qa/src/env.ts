// Loads the repo-root .env (if present) and makes sure Claude is called directly.
import { existsSync } from "node:fs";
import { resolve } from "node:path";

for (const p of [resolve(process.cwd(), ".env"), resolve(process.cwd(), "../.env")]) {
  if (existsSync(p)) {
    process.loadEnvFile(p);
    break;
  }
}
// Some dev shells route Anthropic traffic through a proxy; this example talks to the real API.
delete process.env.ANTHROPIC_BASE_URL;
