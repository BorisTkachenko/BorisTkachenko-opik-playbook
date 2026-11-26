import "./env.js";
import { askGuide, NOTES } from "./guide.js";
import { DEMO_QUESTIONS } from "./questions.js";
import { verifyQuotes } from "./notes.js";

for (const question of DEMO_QUESTIONS) {
  const answer = await askGuide(question);
  const checks = verifyQuotes(answer, NOTES);
  console.log(`Q: ${question}\nA: ${answer}`);
  console.log(`   quotes: ${checks.filter((c) => c.verbatim).length}/${checks.length} verbatim\n`);
}
