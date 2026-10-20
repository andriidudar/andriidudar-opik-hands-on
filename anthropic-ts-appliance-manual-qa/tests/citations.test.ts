import { describe, expect, it } from "vitest";
import { checkCitations, extractQuotes } from "../src/citations.js";

const manual = "The boiler needs 8 minutes to reach brewing temperature.\nThe group head needs 20 minutes.";

describe("citations", () => {
  it("extracts every quote, including multi-line ones", () => {
    const answer = "A <quote>first</quote> and <quote>second\nline</quote>";
    expect(extractQuotes(answer)).toEqual(["first", "second\nline"]);
  });

  it("accepts quotes that appear in the manual even if whitespace differs", () => {
    const answer = "<quote>The boiler needs 8 minutes to reach brewing temperature. The group head needs 20 minutes.</quote>";
    expect(checkCitations(answer, manual).ok).toBe(true);
  });

  it("flags a paraphrased quote", () => {
    const answer = "<quote>The boiler needs eight minutes</quote>";
    const check = checkCitations(answer, manual);
    expect(check.ok).toBe(false);
    expect(check.missing).toEqual(["The boiler needs eight minutes"]);
  });

  it("does not count an answer without quotes as cited", () => {
    expect(checkCitations("Wait 20 minutes.", manual).ok).toBe(false);
  });
});
