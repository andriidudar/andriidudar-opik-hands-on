import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export type Appliance = "combi-oven" | "bread-maker" | "espresso-machine";

export const APPLIANCE_NAMES: Record<Appliance, string> = {
  "combi-oven": "Hearthline CO-900 Combi Oven",
  "bread-maker": "Loafwright BM-4 Bread Maker",
  "espresso-machine": "Brasa Ristretto E2 Espresso Machine",
};

export function loadManual(appliance: Appliance): string {
  const url = new URL(`../docs/${appliance}.md`, import.meta.url);
  return readFileSync(fileURLToPath(url), "utf8");
}
