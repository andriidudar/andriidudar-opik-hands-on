import "dotenv/config";

export const PROJECT = "ollama-langchainjs-stargazing-rag";

// Opik defaults for a local self-hosted stack; a real .env or shell value wins.
process.env.OPIK_URL_OVERRIDE ??= "http://localhost:5173/api/";
process.env.OPIK_WORKSPACE ??= "default";
// The Opik client reads the project from the environment, so every trace lands in PROJECT.
process.env.OPIK_PROJECT_NAME ??= PROJECT;

export const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL ?? "http://localhost:11434";
export const CHAT_MODEL = process.env.CHAT_MODEL ?? "llama3.2:1b";
export const EMBED_MODEL = process.env.EMBED_MODEL ?? "nomic-embed-text";
export const TOP_K = 3;
