import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    // Use z.coerce.date() so both unquoted (2026-10-24) and quoted ("2026-10-24") strings are accepted safely
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default('Not This Time Team'),
    category: z.string().default('Mindful Eating'),
    readingTime: z.string().default('4 min read'),
    image: z.string().optional(),
    tags: z.array(z.string()).default([]),
  }),
});

export const collections = {
  blog: blogCollection,
};
