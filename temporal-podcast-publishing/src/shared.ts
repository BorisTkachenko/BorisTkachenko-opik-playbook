export const TASK_QUEUE = 'podcast-publishing';

export interface EpisodeInput {
  episodeId: string; // e.g. "ep41"
  title: string;
  transcript: string; // full text of the episode transcript
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
