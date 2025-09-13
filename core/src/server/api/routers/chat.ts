import { z } from "zod";
import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

export const chatRouter = createTRPCRouter({
  // Get chat history (mock for now)
  getHistory: publicProcedure.query(() => {
    // Mock chat history
    return [
      {
        id: "1",
        role: "user" as const,
        content: "Hello!",
        timestamp: new Date("2024-01-01T10:00:00Z"),
      },
      {
        id: "2",
        role: "assistant" as const,
        content: "Hello! How can I help you today?",
        timestamp: new Date("2024-01-01T10:00:01Z"),
      },
    ];
  }),

  // Save message (mock for now)
  saveMessage: publicProcedure
    .input(
      z.object({
        role: z.enum(["user", "assistant"]),
        content: z.string(),
      })
    )
    .mutation(({ input }) => {
      // Mock implementation - just log for now
      console.log(`Mock: Saving message - ${input.role}: ${input.content}`);
      return {
        id: Math.random().toString(36).substr(2, 9),
        ...input,
        timestamp: new Date(),
      };
    }),
});
