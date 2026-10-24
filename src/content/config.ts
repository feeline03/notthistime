import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    // z.coerce.date() accepts both raw dates and quoted date strings
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default('Not This Time Team'),
    category: z.string().default('Mindful Eating'),
    readingTime: z.string().default('4 min read'),
    image: z.string().optional(),
    tags: z.array(z.string()).default([]),
    // draft mode: if true, will not be published
    draft: z.boolean().default(false),
  }),
});

export const collections = {
  blog: blogCollection,
};
