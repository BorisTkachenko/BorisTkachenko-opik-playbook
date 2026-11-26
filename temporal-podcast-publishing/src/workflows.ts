import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';
import type { EpisodeInput, PublishResult } from './shared';

const { draftShowNotes, draftSocialBlurb, uploadToCdn } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 minute',
  retry: { initialInterval: '1 second', backoffCoefficient: 2, maximumAttempts: 5 },
});

/**
 * Publish one episode. Each step is an activity Temporal persists: if the CDN
 * upload fails, only the upload is retried; the two LLM drafts are never paid
 * for twice.
 */
export async function publishEpisode(episode: EpisodeInput): Promise<PublishResult> {
  const showNotes = await draftShowNotes(episode);
  const socialBlurb = await draftSocialBlurb(episode, showNotes);
  const cdn = await uploadToCdn(episode, showNotes, socialBlurb);
  return { episodeId: episode.episodeId, showNotes, socialBlurb, cdn };
}
