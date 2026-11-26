/**
 * Opik tracing shared by the two processes (the starter in demo.ts and the
 * worker). One Opik trace is created by the starter; the worker attaches its
 * spans to it using the ids that travel inside the workflow input.
 */
import { activityInfo } from '@temporalio/activity';
import { Opik, OpikSpanType, isTracingActive, setTracingActive, type Span, type SpanType, type Trace } from 'opik';
import './env';
import type { TraceLink } from './shared';

// One client per process, pinned to the project. Without the explicit
// projectName spans would land in "Default Project".
export const opik = new Opik({ projectName: process.env.OPIK_PROJECT_NAME });

/**
 * A Trace handle for a trace that another process already created.
 *
 * `opik.trace({ id })` would POST a second create for that id, and the backend
 * lets the later write replace the first one's input and metadata (observed:
 * both came back null). So the create is suppressed: tracing is switched off
 * for this one synchronous call, which builds the handle without queueing
 * anything, and then restored. Spans made from the handle are sent normally.
 */
function attachToTrace(traceId: string): Trace {
  const wasActive = isTracingActive();
  setTracingActive(false);
  try {
    return opik.trace({ id: traceId, name: 'remote-trace-handle' });
  } finally {
    setTracingActive(wasActive);
  }
}

/**
 * Run one Temporal activity attempt inside an Opik span that hangs off the
 * starter's span. Temporal calls the activity function again on every retry,
 * so each attempt opens its own span: a failed attempt is closed with the
 * error (red in the trace tree) and the retry shows up as its sibling.
 * Without a link the activity just runs untraced.
 */
export async function traceActivityAttempt<T>(
  link: TraceLink | undefined,
  name: string,
  type: SpanType,
  input: Record<string, unknown>,
  run: (span: Span | undefined) => Promise<T>,
): Promise<T> {
  if (!link) return run(undefined);
  const info = activityInfo();
  const span = attachToTrace(link.traceId).span({
    name: `${name} (attempt ${info.attempt})`,
    type,
    parentSpanId: link.parentSpanId,
    input,
    metadata: { process: { role: 'worker', pid: process.pid }, temporal: { workflowId: info.workflowExecution?.workflowId, activity: info.activityType, attempt: info.attempt } },
  });
  try {
    const output = await run(span);
    span.update({ output: { result: output as unknown }, endTime: new Date() });
    return output;
  } catch (err) {
    const e = err as Error;
    // errorInfo is what makes Opik mark the span as failed and show the traceback.
    span.update({ errorInfo: { exceptionType: e.name, message: e.message, traceback: e.stack ?? '' }, endTime: new Date() });
    throw err;
  }
}

export { OpikSpanType };
