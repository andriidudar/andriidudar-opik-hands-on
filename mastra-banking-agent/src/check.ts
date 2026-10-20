// Reads the project back from Opik's REST API and prints each trace as a tree:
// span type, name, tool arguments/results, tokens and cost. Run after `npm run demo`.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});

const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/+$/, "");
const project = process.env.OPIK_PROJECT_NAME ?? "mastra-banking-agent";
const headers: Record<string, string> = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

const get = async (path: string): Promise<any> => {
  const res = await fetch(`${base}/v1/private${path}`, { headers });
  if (!res.ok) throw new Error(`${path} -> HTTP ${res.status}`);
  return res.json();
};
const short = (v: unknown, n = 110) => (JSON.stringify(v) ?? "").slice(0, n);

// The agent loop spans we care about: llm (chat) and tool (execute_tool).
const traces = (await get(`/traces?project_name=${encodeURIComponent(project)}&size=50`)).content as any[];
console.log(`Project "${project}": ${traces.length} traces`);
for (const t of traces.reverse()) {
  const spans = (await get(`/spans?project_name=${encodeURIComponent(project)}&trace_id=${t.id}&size=200`)).content as any[];
  const byType = spans.reduce<Record<string, number>>((m, s) => ((m[s.type] = (m[s.type] ?? 0) + 1), m), {});
  console.log(`\nTRACE ${t.id}  spans=${spans.length} ${short(byType, 80)}`);
  console.log(`  tokens=${t.usage?.total_tokens ?? "?"}  cost=$${t.total_estimated_cost ?? "null"}`);
  for (const s of spans.filter((x) => x.type === "tool" || x.type === "llm").sort((a, b) => a.start_time.localeCompare(b.start_time))) {
    if (s.type === "tool") {
      console.log(`  [tool] ${s.name}  args=${short(s.input?.["gen_ai.tool.call.arguments"])}  result=${short(s.output?.["gen_ai.tool.call.result"], 70)}`);
    } else {
      console.log(`  [llm]  ${s.name}  model=${s.model}  tokens=${s.usage?.total_tokens}  cost=$${s.total_estimated_cost ?? "null"}`);
    }
  }
}
