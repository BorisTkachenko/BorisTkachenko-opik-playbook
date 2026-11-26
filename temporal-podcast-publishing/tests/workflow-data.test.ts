import * as fs from 'node:fs';
import * as path from 'node:path';
import { describe, expect, it } from 'vitest';

describe('episode data', () => {
  it('ships a timestamped transcript for each episode the demo publishes', () => {
    const dir = path.join(__dirname, '..', 'data');
    const files = fs.readdirSync(dir).filter((f) => f.endsWith('.txt'));
    expect(files.length).toBeGreaterThanOrEqual(2);
    for (const f of files) {
      expect(fs.readFileSync(path.join(dir, f), 'utf8')).toMatch(/\[\d\d:\d\d\]/);
    }
  });
});
