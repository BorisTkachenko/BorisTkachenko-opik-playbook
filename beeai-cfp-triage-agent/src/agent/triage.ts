// A BeeAI ReAct agent with the four CFP tools. A fresh agent (and memory) per
// proposal keeps each proposal a separate run.
import { ReActAgent } from "beeai-framework/agents/react/agent";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { getProposal } from "../data/store.ts";
import {
  duplicateCheckTool,
  scoreAbstractTool,
  speakerHistoryTool,
  trackCapacityTool,
} from "../tools/index.ts";
import { triagePrompt } from "./prompt.ts";

export function createTriageAgent(): ReActAgent {
  return new ReActAgent({
    llm: new OpenAIChatModel("gpt-4o-mini"),
    tools: [speakerHistoryTool, trackCapacityTool, scoreAbstractTool, duplicateCheckTool],
    memory: new UnconstrainedMemory(),
  });
}

export async function triageProposal(id: string): Promise<string> {
  const proposal = getProposal(id);
  if (!proposal) throw new Error(`Unknown proposal "${id}"`);
  const response = await createTriageAgent().run(
    { prompt: triagePrompt(proposal) },
    { execution: { maxRetriesPerStep: 3, totalMaxRetries: 10, maxIterations: 10 } },
  );
  return response.result.text;
}
