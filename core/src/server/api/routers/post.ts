import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";
import { posts } from "~/server/db/schema"; // Keep for later use

// Mock data store (in-memory for now)
let mockPosts: Array<{ id: number; name: string; createdAt: Date }> = [
  { id: 1, name: "Welcome to GalilAI!", createdAt: new Date("2024-01-01") },
  { id: 2, name: "Getting started with AI", createdAt: new Date("2024-01-02") },
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
    .mutation(async ({ ctx, input }) => {
      // Mock database insert - add to in-memory store
      const newPost = {
        id: mockPosts.length + 1,
        name: input.name,
        createdAt: new Date(),
      };
      mockPosts.push(newPost);
      
      // Simulate async operation
      await new Promise(resolve => setTimeout(resolve, 100));
    }),

  getLatest: publicProcedure.query(async ({ ctx }) => {
    // Mock database query - return latest post from in-memory store
    await new Promise(resolve => setTimeout(resolve, 50)); // Simulate async
    
    if (mockPosts.length === 0) {
      return null;
    }
    
    // Sort by createdAt descending and return the first (latest)
    const sortedPosts = [...mockPosts].sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
    return sortedPosts[0];
  }),
});
