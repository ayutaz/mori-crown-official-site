import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

describe('navigation contract', () => {
  const layoutPath = path.join(process.cwd(), 'src/layouts/BaseLayout.astro');
  const source = readFileSync(layoutPath, 'utf8');

  it('contains required top navigation labels from site spec', () => {
    const requiredLabels = ['ホーム', 'ニュース', 'タレント', '配信', 'ショップ', 'オーディション'];
    for (const label of requiredLabels) {
      expect(source.includes(label), `${label} is missing in global nav`).toBe(true);
    }
  });

  it('contains required utility links', () => {
    const requiredLabels = ['ファン活動ガイド', '会社概要', 'お問い合わせ'];
    for (const label of requiredLabels) {
      expect(source.includes(label), `${label} is missing in utility nav`).toBe(true);
    }
  });
});
