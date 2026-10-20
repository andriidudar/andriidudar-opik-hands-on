import { ensureAnswerRelevanceRule } from "./opik-rest";

const { id, created } = await ensureAnswerRelevanceRule();
console.log(`${created ? "Created" : "Found existing"} online rule answer_relevance (${id})`);
