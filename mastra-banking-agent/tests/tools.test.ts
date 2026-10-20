// With OPIK_TRACK_DISABLE=true mastra.ts builds no exporter, so importing the
// Mastra instance and running the tools does not need Opik or a model key.
import { describe, expect, it } from "vitest";
import { getBalanceTool, listTransactionsTool } from "../src/tools.ts";
import { opikHeaders, mastra } from "../src/mastra.ts";

describe("tools and tracing config", () => {
  it("runs a tool that the agent loop would trace, with tracking disabled", async () => {
    process.env.OPIK_TRACK_DISABLE = "true";
    const out = await getBalanceTool.execute!({ account_id: "SAV-7731" }, {} as never);
    expect(out).toMatchObject({ account_id: "SAV-7731", balance: 12950 });
    const tx = (await listTransactionsTool.execute!({ account_id: "CHK-9054", limit: 2 }, {} as never)) as any;
    expect(tx.count).toBe(2);
  });
  it("registers the banking agent on the Mastra instance", () => {
    expect(mastra.getAgent("bankingAgent").name).toBe("fernbank-assistant");
  });
  it("sends the project name and workspace, and an API key only when set", () => {
    expect(opikHeaders({ OPIK_WORKSPACE: "w" })).toEqual({ "Comet-Workspace": "w", projectName: "mastra-banking-agent" });
    expect(opikHeaders({ OPIK_API_KEY: "k" }).Authorization).toBe("k");
  });
});
