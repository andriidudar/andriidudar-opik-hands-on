import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

export interface Note {
  slug: string;
  title: string;
  body: string;
}

// Reads every data/*.md file; the first "# " line is the title.
export function loadNotes(dir: string): Note[] {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .map((file) => {
      const body = readFileSync(path.join(dir, file), "utf8").trim();
      const title = body.split("\n")[0].replace(/^#\s*/, "");
      return { slug: file.replace(/\.md$/, ""), title, body };
    });
}

const STOP = new Set(["the", "and", "for", "with", "that", "this", "what", "when", "how", "why", "are", "can", "does", "from", "have", "has", "was", "its", "it's", "you", "your", "not", "but", "too", "get", "all", "any", "should", "would", "about", "into", "they", "them", "there", "then", "than"]);

export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z][a-z-]{2,}/g) ?? [])
    .filter((w) => !STOP.has(w))
    .map((w) => w.replace(/(ies)$/, "y").replace(/(es|s)$/, ""));
}

// Keyword-overlap retrieval: score = number of distinct query words that also
// appear in the note. Plenty for seven short fictional notes.
export function retrieve(notes: Note[], query: string, k = 2): Note[] {
  const q = new Set(tokenize(query));
  return notes
    .map((note) => {
      const words = new Set(tokenize(note.body));
      let score = 0;
      for (const w of q) if (words.has(w)) score += 1;
      // A plant named in the question outweighs incidental overlaps.
      for (const w of tokenize(note.title)) if (q.has(w)) score += 3;
      return { note, score };
    })
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, k)
    .map((s) => s.note);
}

export function buildSystemPrompt(notes: Note[]): string {
  const context = notes.length
    ? notes.map((n) => n.body).join("\n\n---\n\n")
    : "(no matching notes)";
  return `You are Sprout, a friendly home-gardening assistant.
Answer in two to four sentences, using the care notes below when they apply.
If the notes do not cover the question, say so briefly and give general advice only if you are confident.

CARE NOTES
${context}`;
}
