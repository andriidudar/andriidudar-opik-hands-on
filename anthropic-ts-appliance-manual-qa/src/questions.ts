import type { Appliance } from "./manuals.js";

export interface Question {
  appliance: Appliance;
  question: string;
}

export const QUESTIONS: Question[] = [
  { appliance: "combi-oven", question: "My oven says 'Descale now'. What still works, and how long does descaling take?" },
  { appliance: "combi-oven", question: "Is limescale damage covered by the warranty?" },
  { appliance: "bread-maker", question: "Can I set the delay timer for a loaf made with fresh milk?" },
  { appliance: "bread-maker", question: "The display shows E02. What do I do?" },
  { appliance: "espresso-machine", question: "How long should I let the machine warm up before the first shot?" },
  { appliance: "espresso-machine", question: "What does the machine do when the water tank is nearly empty?" },
];
