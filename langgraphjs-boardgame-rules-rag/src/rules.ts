import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

export interface RuleChunk {
  game: string;
  section: string;
  text: string;
}

// Split each rulebook into one chunk per "## " section, prefixed with the game title
// so a retrieved chunk is understandable on its own.
export function chunkRulebook(markdown: string): RuleChunk[] {
  const lines = markdown.split("\n");
  const title = (lines[0] ?? "").replace(/^#\s*/, "").trim();
  const game = title.replace(/\s*\(.*\)$/, "");
  const chunks: RuleChunk[] = [];
  let section: string | null = null;
  let body: string[] = [];
  const flush = () => {
    if (section) {
      chunks.push({ game, section, text: `${title} - ${section}: ${body.join(" ").trim()}` });
    }
  };
  for (const line of lines.slice(1)) {
    if (line.startsWith("## ")) {
      flush();
      section = line.slice(3).trim();
      body = [];
    } else if (line.trim()) {
      body.push(line.trim());
    }
  }
  flush();
  return chunks;
}

export function loadRulebooks(dir: string): RuleChunk[] {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .flatMap((f) => chunkRulebook(readFileSync(join(dir, f), "utf8")));
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i]! * b[i]!;
    na += a[i]! ** 2;
    nb += b[i]! ** 2;
  }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}

export function topK<T>(query: number[], items: { vec: number[]; item: T }[], k: number): T[] {
  return items
    .map((x) => ({ item: x.item, score: cosine(query, x.vec) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((x) => x.item);
}
