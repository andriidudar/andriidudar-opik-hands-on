// Tiny helpers over Opik's REST API (no SDK needed for any of this).
// Everything here talks to Opik, so run these scripts via the Opik lock if
// you share one instance.
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(process.cwd(), ".env"), quiet: true });
config({ path: path.resolve(process.cwd(), "../.env"), quiet: true });

export const PROJECT = "vercel-ai-sveltekit-garden-chat";
export const RULE_NAME = "answer_relevance";

const BASE = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/?$/, "/");
const headers: Record<string, string> = {
  "Content-Type": "application/json",
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
};

export async function api(method: string, route: string, body?: unknown): Promise<Response> {
  const res = await fetch(BASE + route.replace(/^\//, ""), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${method} ${route} -> ${res.status}: ${await res.text()}`);
  return res;
}

export async function ensureProject(): Promise<string> {
  const found = await (await api("GET", `v1/private/projects?name=${encodeURIComponent(PROJECT)}`)).json();
  const exact = found.content?.find((p: { name: string }) => p.name === PROJECT);
  if (exact) return exact.id;
  await api("POST", "v1/private/projects", { name: PROJECT });
  return ensureProject();
}

// Find-or-create: running this twice never makes a second rule.
export async function ensureAnswerRelevanceRule(): Promise<{ id: string; created: boolean }> {
  const projectId = await ensureProject();
  const list = await (
    await api("GET", `v1/private/automations/evaluators?project_id=${projectId}&name=${RULE_NAME}`)
  ).json();
  const existing = list.content?.find((r: { name: string }) => r.name === RULE_NAME);
  if (existing) return { id: existing.id, created: false };

  // An online-evaluation rule is a stored LLM-as-judge prompt attached to a
  // project. Opik runs it server-side on every new trace (sampling_rate 1 =
  // all of them) and writes the result back as a feedback score named after
  // the schema entry. The judge uses the OpenAI key already stored in Opik's
  // own provider settings; this app never sends a key.
  await api("POST", "v1/private/automations/evaluators", {
    name: RULE_NAME,
    type: "llm_as_judge",
    project_ids: [projectId],
    sampling_rate: 1,
    enabled: true,
    code: {
      model: { name: "gpt-4o-mini", temperature: 0 },
      messages: [
        {
          role: "USER",
          content:
            "You grade a gardening assistant. Decide whether the ANSWER directly addresses the QUESTION " +
            "(admitting that it lacks information about the topic counts as relevant only if the question " +
            "was actually about gardening).\n\nQUESTION (the chat so far, as JSON):\n{{input}}\n\nANSWER:\n{{output}}\n\n" +
            "Return 1 if the answer is relevant to the last user question, otherwise 0.",
        },
      ],
      variables: { input: "input", output: "output" },
      schema: [
        {
          name: RULE_NAME,
          type: "INTEGER",
          description: "1 if the answer addresses the last user question, 0 if it does not",
        },
      ],
    },
  });
  const after = await (
    await api("GET", `v1/private/automations/evaluators?project_id=${projectId}&name=${RULE_NAME}`)
  ).json();
  return { id: after.content[0].id, created: true };
}

export interface TraceRow {
  id: string;
  name: string;
  thread_id?: string;
  input?: unknown;
  output?: unknown;
  usage?: Record<string, number>;
  total_estimated_cost?: number;
  feedback_scores?: { name: string; value: number; reason?: string }[];
}

// Every trace in the project, including the judge's own runs: Opik logs each
// online-rule execution as a trace named "online_evaluation" in the same project.
export async function listAllTraces(): Promise<TraceRow[]> {
  const res = await (
    await api("GET", `v1/private/traces?project_name=${encodeURIComponent(PROJECT)}&size=200`)
  ).json();
  return res.content ?? [];
}

// Only the chat turns this app produced.
export async function listTraces(): Promise<TraceRow[]> {
  return (await listAllTraces()).filter((t) => t.name !== "online_evaluation");
}

// Deletes traces only. The online rule is left alone, so a re-run is still scored.
export async function deleteAllTraces(): Promise<number> {
  const ids = (await listAllTraces()).map((t) => t.id);
  if (ids.length) await api("POST", "v1/private/traces/delete", { ids });
  return ids.length;
}
