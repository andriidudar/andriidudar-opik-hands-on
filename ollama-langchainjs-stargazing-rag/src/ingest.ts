import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { Document } from "@langchain/core/documents";
import type { EmbeddingsInterface } from "@langchain/core/embeddings";
import { MemoryVectorStore } from "@langchain/classic/vectorstores/memory";

/** Split one markdown file into one Document per "## " section, keeping the title for context. */
export function splitSections(file: string, markdown: string): Document[] {
  const title = /^#\s+(.+)$/m.exec(markdown)?.[1]?.trim() ?? file;
  const docs: Document[] = [];
  for (const block of markdown.split(/^## /m).slice(1)) {
    const [heading = "", ...body] = block.split("\n");
    const text = body.join("\n").trim();
    if (!text) continue;
    docs.push(
      new Document({
        pageContent: `${heading.trim()}\n${text}`,
        metadata: { source: file, title, section: heading.trim() },
      }),
    );
  }
  return docs;
}

export async function loadDocs(dir: string): Promise<Document[]> {
  const files = (await readdir(dir)).filter((f) => f.endsWith(".md")).sort();
  const perFile = await Promise.all(
    files.map(async (f) => splitSections(f, await readFile(path.join(dir, f), "utf8"))),
  );
  return perFile.flat();
}

/** Embed every section with the given (local) embeddings and keep them in memory. */
export async function buildIndex(docs: Document[], embeddings: EmbeddingsInterface) {
  return MemoryVectorStore.fromDocuments(docs, embeddings);
}
