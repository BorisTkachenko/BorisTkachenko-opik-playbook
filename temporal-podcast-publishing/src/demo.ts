/**
 * Self-contained demo: start a throwaway Temporal dev server, spawn the worker
 * as a separate OS process, publish two episodes from this (client) process,
 * then shut everything down.
 */
import './env';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { spawn, type ChildProcess } from 'node:child_process';
import { Client } from '@temporalio/client';
import { TestWorkflowEnvironment } from '@temporalio/testing';
import { requireEnv } from './env';
import { TASK_QUEUE, type EpisodeInput } from './shared';
import type { publishEpisode } from './workflows';

const PORT = Number(process.env.TEMPORAL_PORT ?? 7243);

const EPISODES: { episodeId: string; title: string; file: string }[] = [
  { episodeId: 'ep41', title: 'The Sourdough Server Rack', file: 'ep41-sourdough-server-rack.txt' },
  { episodeId: 'ep42', title: 'The Parrot and the Barometer', file: 'ep42-parrot-barometer.txt' },
];

function loadEpisode(e: (typeof EPISODES)[number]): EpisodeInput {
  const transcript = fs.readFileSync(path.join(__dirname, '..', 'data', e.file), 'utf8');
  return { episodeId: e.episodeId, title: e.title, transcript };
}

function startWorkerProcess(address: string): Promise<ChildProcess> {
  const tsxBin = path.join(__dirname, '..', 'node_modules', '.bin', 'tsx');
  const child = spawn(tsxBin, [path.join(__dirname, 'worker.ts')], {
    env: { ...process.env, TEMPORAL_ADDRESS: address },
    stdio: ['ignore', 'pipe', 'inherit'],
  });
  return new Promise((resolve, reject) => {
    child.stdout!.on('data', (chunk: Buffer) => {
      process.stdout.write(`[worker] ${chunk}`);
      if (chunk.toString().includes('WORKER_READY')) resolve(child);
    });
    child.on('exit', (code) => reject(new Error(`Worker exited early with code ${code}`)));
  });
}

async function main() {
  requireEnv('OPENAI_API_KEY');

  console.log(`Starting local Temporal dev server on port ${PORT}...`);
  const env = await TestWorkflowEnvironment.createLocal({ server: { port: PORT } });
  const address = `127.0.0.1:${PORT}`;
  const worker = await startWorkerProcess(address);
  const client = new Client({ connection: env.connection });

  try {
    for (const meta of EPISODES) {
      const episode = loadEpisode(meta);
      console.log(`\n=== ${episode.episodeId}: ${episode.title}`);
      const handle = await client.workflow.start<typeof publishEpisode>('publishEpisode', {
        taskQueue: TASK_QUEUE,
        workflowId: `publish-${episode.episodeId}-${Date.now()}`,
        args: [episode],
      });
      const result = await handle.result();
      console.log(`Summary: ${result.showNotes.summary}`);
      console.log(`Chapters: ${result.showNotes.chapters.map((c) => `${c.timestamp} ${c.title}`).join(' | ')}`);
      console.log(`Blurb: ${result.socialBlurb}`);
      console.log(`CDN: ${result.cdn.url} (${result.cdn.bytes} bytes, uploaded on attempt ${result.cdn.attempt})`);
    }
  } finally {
    console.log('\nShutting down...');
    worker.kill('SIGINT');
    await new Promise((resolve) => worker.once('exit', resolve));
    await env.teardown();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
