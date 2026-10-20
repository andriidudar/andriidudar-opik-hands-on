import "./env.js";
import { checkCitations } from "./citations.js";
import { loadManual } from "./manuals.js";
import { answerQuestion } from "./qa.js";
import { QUESTIONS } from "./questions.js";

for (const { appliance, question } of QUESTIONS) {
  const answer = await answerQuestion(appliance, question);
  const check = checkCitations(answer, loadManual(appliance));
  console.log(`\nQ [${appliance}]: ${question}\nA: ${answer}`);
  console.log(`   quotes: ${check.quotes.length}, not verbatim: ${check.missing.length}`);
}
