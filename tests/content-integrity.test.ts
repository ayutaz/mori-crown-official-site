import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

import matter from 'gray-matter';
import { describe, expect, it } from 'vitest';

const root = process.cwd();

function readCollection(dir: string) {
  const absDir = path.join(root, dir);
  return readdirSync(absDir)
    .filter((file) => file.endsWith('.md'))
    .map((file) => {
      const slug = file.replace(/\.md$/, '');
      const raw = readFileSync(path.join(absDir, file), 'utf8');
      const parsed = matter(raw);
      return {
        slug,
        data: parsed.data as Record<string, unknown>
      };
    });
}

describe('talent content integrity', () => {
  const talents = readCollection('src/content/talents');

  it('has at least 5 talents', () => {
    expect(talents.length).toBeGreaterThanOrEqual(5);
  });

  it('every talent has standing and turnaround images in public/', () => {
    for (const talent of talents) {
      const image = talent.data.image as string;
      const turnaround = talent.data.turnaround as string;

      expect(image, `${talent.slug}: image is missing`).toBeTruthy();
      expect(turnaround, `${talent.slug}: turnaround is missing`).toBeTruthy();

      const standingPath = path.join(root, 'public', image.replace(/^\//, ''));
      const turnaroundPath = path.join(root, 'public', turnaround.replace(/^\//, ''));

      expect(existsSync(standingPath), `${talent.slug}: ${standingPath} not found`).toBe(true);
      expect(existsSync(turnaroundPath), `${talent.slug}: ${turnaroundPath} not found`).toBe(true);
    }
  });

  it('every talent has valid hex theme color', () => {
    const hexColor = /^#[0-9A-Fa-f]{6}$/;
    for (const talent of talents) {
      expect(talent.data.color).toMatch(hexColor);
    }
  });
});

describe('news content integrity', () => {
  const talents = readCollection('src/content/talents');
  const news = readCollection('src/content/news');
  const talentSlugs = new Set(talents.map((talent) => talent.slug));
  const allowedCategories = new Set(['配信', 'イベント', 'グッズ', '重要']);

  it('news category values are from allowed set', () => {
    for (const item of news) {
      expect(allowedCategories.has(item.data.category as string), `${item.slug}: invalid category`).toBe(true);
    }
  });

  it('news relatedTalents reference existing talent slugs', () => {
    for (const item of news) {
      const related = (item.data.relatedTalents as string[] | undefined) ?? [];
      for (const slug of related) {
        expect(talentSlugs.has(slug), `${item.slug}: unknown talent slug ${slug}`).toBe(true);
      }
    }
  });

  it('internal CTA links use rooted path format', () => {
    for (const item of news) {
      const ctaHref = item.data.ctaHref as string | undefined;
      if (!ctaHref || /^https?:\/\//.test(ctaHref)) {
        continue;
      }
      expect(ctaHref.startsWith('/'), `${item.slug}: ctaHref must start with /`).toBe(true);
      expect(ctaHref.endsWith('/'), `${item.slug}: ctaHref should end with /`).toBe(true);
    }
  });
});
