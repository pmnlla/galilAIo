import { createAnthropic } from '@ai-sdk/anthropic';
import { streamText, convertToModelMessages, type UIMessage, stepCountIs, tool } from 'ai';
import { z } from 'zod';
import fs from 'node:fs';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

const anthropic = createAnthropic();


const getName = tool({
    description: 'Get the name of a person based on their ID or description',
    inputSchema: z.object({
      personId: z.string().describe('The ID or description of the person'),
    }),
    execute: async ({ personId }: { personId: string }) => {
      // Mock implementation - in real app this would query a database
      const mockNames = {
        '1': 'Alice Johnson',
        '2': 'Bob Smith', 
        '3': 'Charlie Brown',
        'ceo': 'Sarah Wilson',
        'manager': 'Mike Davis',
        'developer': 'Emma Thompson'
      };

      
      const name = mockNames[personId as keyof typeof mockNames] || `Person with ID: ${personId}`;
      return { name, personId };
    },
  });

/*
const result = await generateText({
  model: anthropic('claude-3-5-sonnet-20241022'),
  tools: {
    computer: anthropic.tools.computer_20241022({
      // ...
      async execute({ action, coordinate, text }) {
        switch (action) {
          case 'screenshot': {
            return {
              type: 'image',
              data: fs
                .readFileSync('./data/screenshot-editor.png')
                .toString('base64'),
            };
          }
          default: {
            return `executed ${action}`;
          }
        }
      },

      // map to tool result content for LLM consumption:
      toModelOutput(result) {
        return {
          type: 'content',
          value:
            typeof result === 'string'
              ? [{ type: 'text', text: result }]
              : [{ type: 'image', data: result.data, mediaType: 'image/png' }],
        };
      },
    }),
  },
  // ...
});
*/

// always return "C:\Users\aaron\Pictures\Screenshots\test.png"
  
const getUserPaper = tool({
    description: 'Get the current image from the camera',
    inputSchema: z.object({}),
    execute: async (): Promise<{ type: 'image'; data: string } | string> => {
      try {
        const response = await fetch('http://localhost:8000/current-frame-correction');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const arrayBuffer = await response.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        return {
          type: 'image',
          data: buffer.toString('base64'),
        };
      } catch (error) {
        console.error('Error fetching screenshot:', error);
        return 'Error fetching screenshot. Make sure the screenshot server is running at http://localhost:8000';
      }
    },
    toModelOutput(result) {
      return {
        type: 'content',
        value:
          typeof result === 'string'
            ? [{ type: 'text', text: result }]
            : [{ type: 'media', data: result.data, mediaType: 'image/png' }],
      };
    },
  });

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = await streamText({
    model: anthropic('claude-3-7-sonnet-20250219'),
    messages: convertToModelMessages(messages),
    system: `You are a helpful AI tutor. Your goal is to help guide the user through a task and make the understand how to break down a problem and how to approach its solution.

    Do not be overly agreeable, if the user is wrong point it out. Your job is to debate and argue. 

    Do not provide the student with the answer.

    Do provide small hints and break down concepts relating to the problem. 

    Do act in good faith and use friendly language and tonality with the student.

    Keep the conversation friendly and engaging.

    Use the screenshot tool to see what the student is currently working on.

    Remeber, you are a tutor, the user is a student.
`,
tools: {
    // getName,
    getCurrentImage: getUserPaper,
  },

    toolChoice: 'auto', // Enable automatic tool selection
    stopWhen: stepCountIs(3), // Enable multi-step tool execution (up to 3 steps)
  });

  return result.toUIMessageStreamResponse();
}
