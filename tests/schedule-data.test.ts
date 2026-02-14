import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe, expect, it } from 'vitest';

const root = process.cwd();

type Slot = {
  time: string;
  talent: string;
  title: string;
  url: string;
};

type DaySchedule = {
  day: string;
  slots: Slot[];
};

describe('weekly schedule data', () => {
  const schedulePath = path.join(root, 'src/data/schedule.json');
  const schedule = JSON.parse(readFileSync(schedulePath, 'utf8')) as DaySchedule[];

  it('contains 7 unique days', () => {
    expect(schedule).toHaveLength(7);
    expect(new Set(schedule.map((item) => item.day)).size).toBe(7);
  });

  it('all slots contain expected fields and HH:MM time', () => {
    const timePattern = /^([01]\d|2[0-3]):[0-5]\d$/;

    for (const day of schedule) {
      expect(Array.isArray(day.slots), `${day.day}: slots must be array`).toBe(true);

      for (const slot of day.slots) {
        expect(slot.time).toMatch(timePattern);
        expect(slot.talent.length).toBeGreaterThan(0);
        expect(slot.title.length).toBeGreaterThan(0);
        expect(slot.url.length).toBeGreaterThan(0);
      }
    }
  });
});
