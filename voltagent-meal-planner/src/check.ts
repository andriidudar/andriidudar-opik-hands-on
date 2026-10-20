// Verification script: asks Opik's REST API what landed in the project and fails if cost or usage is missing.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";
config({ path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))], quiet: true });

const base = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");
const project = process.env.OPIK_PROJECT_NAME ?? "voltagent-meal-planner";
const headers = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };

type Span = { type: string; name: string; model?: string; provider?: string; usage?: Record<string, number>; total_estimated_cost?: number | null };
const get = async (path: string) => (await fetch(`${base}${path}`, { headers })).json() as Promise<any>;

const traces = (await get(`/v1/private/traces?project_name=${encodeURIComponent(project)}&size=100`)).content ?? [];
const spans: Span[] = (await get(`/v1/private/spans?project_name=${encodeURIComponent(project)}&size=500`)).content ?? [];
console.log(`project=${project} traces=${traces.length} spans=${spans.length}`);
for (const t of traces) console.log(`  trace ${t.id} ${t.name} cost=${t.total_estimated_cost} usage=${JSON.stringify(t.usage)}`);

const llm = spans.filter((s) => s.type === "llm");
const tool = spans.filter((s) => s.type === "tool");
for (const s of llm) console.log(`  llm  ${s.name} model=${s.model} provider=${s.provider} usage=${JSON.stringify(s.usage)} cost=${s.total_estimated_cost}`);
for (const s of tool) console.log(`  tool ${s.name}`);

const bad = llm.filter((s) => s.total_estimated_cost == null || !s.usage?.total_tokens);
console.log(`llm spans=${llm.length} tool spans=${tool.length} llm spans missing cost/usage=${bad.length}`);
process.exit(llm.length > 0 && bad.length === 0 ? 0 : 1);
