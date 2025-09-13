import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";
// TODO: Re-enable database when needed
// import { posts } from "~/server/db/schema";

// Mock data for development
const mockPosts = [
  {
    id: 1,
    name: "Sample Post",
    createdAt: new Date("2024-01-01"),
    updatedAt: new Date("2024-01-01"),
  },
  {
    id: 2,
    name: "Another Post",
    createdAt: new Date("2024-01-02"),
    updatedAt: new Date("2024-01-02"),
  },
];

export const postRouter = createTRPCRouter({
  hello: publicProcedure
    .input(z.object({ text: z.string() }))
    .query(({ input }) => {
      return {
        greeting: `Hello ${input.text}`,
      };
    }),

  create: publicProcedure
    .input(z.object({ name: z.string().min(1) }))
    .mutation(async ({ input }) => {
      // TODO: Re-enable database when needed
      // await ctx.db.insert(posts).values({
      //   name: input.name,
      // });
      
      // Mock implementation - just log for now
      console.log(`Mock: Creating post with name: ${input.name}`);
      const newPost = {
        id: mockPosts.length + 1,
        name: input.name,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      mockPosts.push(newPost);
      return newPost;
    }),

  getLatest: publicProcedure.query(async () => {
    // TODO: Re-enable database when needed
    // const post = await ctx.db.query.posts.findFirst({
    //   orderBy: (posts, { desc }) => [desc(posts.createdAt)],
    // });

    // Mock implementation
    const latestPost = mockPosts.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())[0];
    return latestPost ?? null;
  }),
});
