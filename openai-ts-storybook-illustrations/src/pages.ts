import fs from "node:fs";

export interface StoryPage {
  id: string;
  text: string;
  setting: string;
  mood: string;
}

export interface Story {
  title: string;
  hero: string;
  pages: StoryPage[];
}

export function loadStory(file = "data/pages.json"): Story {
  const story = JSON.parse(fs.readFileSync(file, "utf8")) as Story;
  if (!story.pages?.length) throw new Error(`${file} has no pages`);
  return story;
}

// Variables every brief template may reference.
export function briefVariables(story: Story, page: StoryPage): Record<string, string> {
  return {
    title: story.title,
    hero: story.hero,
    page_text: page.text,
    setting: page.setting,
    mood: page.mood,
  };
}
