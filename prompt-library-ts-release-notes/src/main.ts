import OpenAI from "openai";
import { loadChangeLists } from "./changelogs.js";
import { loadEnv } from "./env.js";
import { PROMPT_V1, PROMPT_V2 } from "./prompts.js";
import { checkRules } from "./rules.js";
import { writeReleaseNote } from "./writer.js";

loadEnv();

async function main(): Promise<void> {
  const client = new OpenAI();
  const entries = loadChangeLists();
  for (const [name, prompt] of [["v1", PROMPT_V1], ["v2", PROMPT_V2]] as const) {
    let passed = 0;
    for (const entry of entries) {
      const text = await writeReleaseNote(client, prompt, entry);
      const r = checkRules(text);
      if (r.plainText && r.summaryShort) passed++;
      console.log(`[${name}] tidepool ${entry.version}\n${text}\n`);
    }
    console.log(`${name}: ${passed}/${entries.length} replies satisfy the local rule checks\n`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
