import { defineCollection, z } from 'astro:content';

const news = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.string(),
    category: z.enum(['配信', 'イベント', 'グッズ', '重要']),
    excerpt: z.string(),
    cover: z.string().optional(),
    relatedTalents: z.array(z.string()).default([]),
    ctaLabel: z.string().optional(),
    ctaHref: z.string().optional()
  })
});

const talents = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    nameKana: z.string(),
    nameEn: z.string(),
    generation: z.string(),
    role: z.string(),
    catchphrase: z.string(),
    summary: z.string(),
    image: z.string(),
    turnaround: z.string(),
    color: z.string(),
    birthday: z.string(),
    height: z.string(),
    fanName: z.string(),
    fanMark: z.string(),
    hashtags: z.object({
      overall: z.string(),
      stream: z.string(),
      fanart: z.string(),
      clip: z.string()
    }),
    streamFocus: z.array(z.string())
  })
});

export const collections = { news, talents };
