// Pure attribute mapping: VoltAgent span attributes -> OpenTelemetry GenAI
// conventions. Kept free of exporter code so it can be unit-tested offline.
export type Attrs = Record<string, unknown>;

// Opik computes `total_estimated_cost` from model + provider + token usage.
// VoltAgent emits the model name but no provider, so we derive it here.
export function providerFor(model: string): string | undefined {
  if (/^(gpt-|o\d|chatgpt|text-embedding)/.test(model)) return "openai";
  if (model.startsWith("claude")) return "anthropic";
  return undefined;
}

export function mapVoltAgentAttributes(attrs: Attrs): void {
  if (attrs["span.type"] === "llm") {
    const model = attrs["llm.model"];
    if (typeof model === "string" && model) {
      attrs["gen_ai.request.model"] = model;
      const provider = providerFor(model);
      if (provider) attrs["gen_ai.provider.name"] = provider;
    }
    for (const key of ["prompt_tokens", "completion_tokens", "total_tokens"]) {
      const value = attrs[`llm.usage.${key}`];
      if (value !== undefined) attrs[`gen_ai.usage.${key}`] = value;
    }
  } else if (attrs["span.type"] === "tool") {
    // Opik types the span as a tool call and shows the arguments as its input.
    attrs["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
    delete attrs["input"];
    delete attrs["tool.parameters"];
  }
}
