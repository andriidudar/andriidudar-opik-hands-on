// Pure helpers: pull <quote> excerpts out of an answer and check them against the manual.

export function extractQuotes(answer: string): string[] {
  return [...answer.matchAll(/<quote>([\s\S]*?)<\/quote>/g)].map((m) => (m[1] ?? "").trim());
}

const normalize = (s: string) => s.replace(/\s+/g, " ").trim();

export interface CitationCheck {
  quotes: string[];
  missing: string[];
  ok: boolean;
}

// A quote is verbatim if it appears in the manual once whitespace is collapsed.
export function checkCitations(answer: string, manual: string): CitationCheck {
  const quotes = extractQuotes(answer);
  const haystack = normalize(manual);
  const missing = quotes.filter((q) => !haystack.includes(normalize(q)));
  return { quotes, missing, ok: quotes.length > 0 && missing.length === 0 };
}
