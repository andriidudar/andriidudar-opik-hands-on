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
  // Not covered by the manual: the right answer is "the manual doesn't say".
  { appliance: "bread-maker", question: "Can I put the bread pan in the dishwasher?" },
];

// Item-level assertions are checked on top of the suite-wide ones. They pin down answers that have
// one correct fact, so a fluent but wrong answer cannot pass.
export const ITEM_ASSERTIONS: Record<string, string[]> = {
  "The display shows E02. What do I do?": [
    "The response says to unplug the machine and let it cool for 60 minutes",
  ],
  "My oven says 'Descale now'. What still works, and how long does descaling take?": [
    "The response says Dry Heat mode still works while Steam Mode and Combi Mode are locked",
    "The response says the descaling cycle takes 75 minutes",
  ],
  "Can I put the bread pan in the dishwasher?": [
    "The response says the manual does not cover dishwasher use and does not claim the pan is or is not dishwasher safe",
  ],
};
