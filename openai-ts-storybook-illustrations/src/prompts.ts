// The "illustration brief": the prompt that turns a story page into an image request.
// Mustache-style {{variables}} are filled from data/pages.json.

export const PROMPT_NAME = "storybook-illustration-brief";

export const BRIEF_V1 = `Illustrate a page from the children's picture book "{{title}}".
Main character: {{hero}}.
Scene: {{setting}}.
Story text on this page: "{{page_text}}"
Mood: {{mood}}.`;

export const BRIEF_V2 = `Illustrate a page from the children's picture book "{{title}}".

Main character (draw them identically on every page): {{hero}}.
Scene: {{setting}}.
Story text on this page, for context only: "{{page_text}}"
Mood: {{mood}}.

House style rules:
- Soft watercolor and colored-pencil look, warm paper texture, gentle rounded shapes.
- Do NOT render any words, letters, captions or speech bubbles anywhere in the image.
- Keep the whole scene child-friendly: no scary shadows, no sharp edges.
- Leave the bottom third of the picture calm and uncluttered so text can be set there.
- Square composition with the main character in the lower-left half.`;

export const V1_CHANGE = "Initial brief: title, hero, scene, story text, mood";
export const V2_CHANGE =
  "Add house-style rules: the story text was being drawn into the pictures as garbled lettering, and Pip's look drifted between pages. v2 forbids rendered words, pins one watercolor style, and reserves space for text.";

export function render(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (_m, key: string) => {
    if (!(key in vars)) throw new Error(`Missing template variable: ${key}`);
    return vars[key];
  });
}

export function templateVariables(template: string): string[] {
  return [...new Set([...template.matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map((m) => m[1]))];
}
