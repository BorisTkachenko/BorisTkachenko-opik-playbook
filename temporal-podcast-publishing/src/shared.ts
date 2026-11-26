export const TASK_QUEUE = 'podcast-publishing';

/** Where in an Opik trace the worker should attach its spans (created by the starter). */
export interface TraceLink {
  traceId: string;
  parentSpanId: string;
}

export interface EpisodeInput {
  episodeId: string; // e.g. "ep41"
  title: string;
  transcript: string; // full text of the episode transcript
  trace?: TraceLink; // set by the starter so the worker can join its trace
}

export interface ShowNotes {
  summary: string;
  chapters: { timestamp: string; title: string }[];
  links: string[];
}

export interface CdnUpload {
  url: string;
  bytes: number;
  attempt: number; // which Temporal attempt finally got the files onto the CDN
}

export interface PublishResult {
  episodeId: string;
  showNotes: ShowNotes;
  socialBlurb: string;
  cdn: CdnUpload;
}
