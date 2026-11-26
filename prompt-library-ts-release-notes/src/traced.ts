import OpenAI from "openai";
import { Opik, type Span, getTrackContext, track } from "opik";
import { trackOpenAI } from "opik-openai";
import { PROJECT_NAME } from "./config.js";
import { type ChangeList } from "./changelogs.js";
import { PROMPT_NAME } from "./prompts.js";
import { type ChatClient, writeReleaseNote } from "./writer.js";

// trackOpenAI wraps the client: every completion is logged with model, token usage and cost.
// It does not read track()'s context, so without `parent` each call would open a separate
// one-span trace. Passing the active span as parent nests the call inside write-release-note.
function trackedClient(opik: Opik, parent: Span): ChatClient {
  return trackOpenAI(new OpenAI(), { client: opik, parent });
}

type ClientFactory = (parent: Span | undefined) => ChatClient;

/**
 * One release note, written with a prompt version pulled from the library.
 *
 * track() makes this the trace root (a general span). Because getPrompt runs inside it,
 * the SDK stamps the prompt's name and commit on the trace metadata, and the wrapped
 * OpenAI call below nests under it as a child span with usage and cost.
 */
export function makeReleaseNoteWriter(
  opik: Opik,
  // Tests inject a stub here; the default wraps a real OpenAI client under the active span.
  clientFor: ClientFactory = (span) => (span ? trackedClient(opik, span) : new OpenAI()),
) {
  return track(
    { name: "write-release-note", projectName: PROJECT_NAME, type: "general" },
    async (entry: ChangeList, version: string): Promise<string> => {
      const prompt = await opik.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
      if (!prompt) throw new Error(`prompt ${PROMPT_NAME} ${version} not found; run the demo first`);

      // Readable metadata next to the automatic prompt link: which version produced this reply.
      getTrackContext()?.trace.update({
        metadata: { prompt_name: PROMPT_NAME, prompt_version: version, prompt_commit: prompt.commit },
      });
      const span = getTrackContext()?.span;
      return writeReleaseNote(clientFor(span), prompt.prompt, entry);
    },
  );
}
