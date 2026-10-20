import { config } from "dotenv";
import path from "node:path";

// This example's .env first, then the repo-root .env. Neither overrides
// variables that are already set in the shell.
config({ path: path.resolve(process.cwd(), ".env"), quiet: true });
config({ path: path.resolve(process.cwd(), "../.env"), quiet: true });
