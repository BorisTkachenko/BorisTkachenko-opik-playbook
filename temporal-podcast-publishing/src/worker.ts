/**
 * The worker process: runs the workflow code and the activities (LLM calls and
 * the CDN upload). `npm run demo` spawns it; `npm run worker` runs it alone
 * against any Temporal server (TEMPORAL_ADDRESS).
 */
import './env';
import { DefaultLogger, NativeConnection, Runtime, Worker } from '@temporalio/worker';
import * as activities from './activities';
import { TASK_QUEUE } from './shared';

async function main() {
  // Keep the console readable: activity retries are reported by the activity itself.
  Runtime.install({ logger: new DefaultLogger('ERROR') });
  const address = process.env.TEMPORAL_ADDRESS ?? 'localhost:7233';
  const connection = await NativeConnection.connect({ address });
  const worker = await Worker.create({
    connection,
    taskQueue: TASK_QUEUE,
    workflowsPath: require.resolve('./workflows'),
    activities,
  });
  console.log(`WORKER_READY on ${address}, task queue "${TASK_QUEUE}"`);
  await worker.run(); // until SIGINT/SIGTERM
  await connection.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
