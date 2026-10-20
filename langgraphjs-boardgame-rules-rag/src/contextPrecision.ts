import { BaseMetric, EvaluationScoreResult } from "opik";
import { z } from "zod";

// Judge: given a question and one retrieved chunk, is the chunk useful for answering?
export type RelevanceJudge = (question: string, chunk: string) => Promise<boolean>;

// Average precision over the ranked chunk list: relevant chunks that appear early count more.
export function averagePrecision(relevance: boolean[]): number {
  let hits = 0;
  let sum = 0;
  relevance.forEach((rel, i) => {
    if (rel) {
      hits += 1;
      sum += hits / (i + 1);
    }
  });
  return hits === 0 ? 0 : sum / hits;
}

// The TypeScript SDK has no ContextPrecision class, so this is our own BaseMetric subclass.
// Subclassing BaseMetric makes it usable in evaluate(): the score shows up as a
// feedback-score column named "context_precision" on each experiment item.
export class ContextPrecision extends BaseMetric {
  readonly validationSchema = z.object({
    input: z.string(),
    context: z.array(z.string()),
  });

  constructor(private readonly judge: RelevanceJudge) {
    super("context_precision");
  }

  async score(raw: unknown): Promise<EvaluationScoreResult> {
    const { input, context } = this.validationSchema.parse(raw);
    const relevance = await Promise.all(context.map((c) => this.judge(input, c)));
    return {
      name: this.name,
      value: averagePrecision(relevance),
      reason: `relevant chunks by rank: ${relevance.map((r) => (r ? "Y" : "N")).join("")}`,
    };
  }
}
