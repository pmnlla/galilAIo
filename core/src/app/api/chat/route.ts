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
        const response = await fetch('http://localhost:8000/screenshot');
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

const createManimAnimation = tool({
    description: 'Create a mathematical animation using Manim. Use this when the user asks for graphs, visualizations, or mathematical concepts that can be animated.',
    inputSchema: z.object({
      type: z.enum(['riemann_sum', 'derivative', 'integral', 'linear_system', 'equation_display']).describe('Type of mathematical animation to create'),
      function: z.string().describe('Mathematical function or equation to visualize (e.g., "x^2", "sin(x)", "2*x + 1")'),
      domain: z.array(z.number()).length(2).describe('Domain range [min, max] for the function'),
      options: z.object({
        sum_type: z.enum(['left', 'right']).optional().describe('For Riemann sums: left or right rectangles'),
        num_rectangles: z.number().optional().describe('Number of rectangles for Riemann sum'),
        point: z.number().optional().describe('Point for derivative tangent line'),
        equations: z.array(z.string()).optional().describe('Multiple equations for linear systems or equation display')
      }).optional().describe('Additional options for the animation')
    }),
    execute: async ({ type, function: func, domain, options = {} }): Promise<{ type: 'video'; data: string; animationId: string } | string> => {
      try {
        const requestBody = {
          type,
          function: func,
          domain,
          options
        };

        const response = await fetch('http://localhost:8002/generate-animation-json', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.status === 'error') {
          return `Error creating animation: ${result.message}`;
        }

        // For now, return the animation ID and status
        // In a full implementation, you might want to serve the video file
        return {
          type: 'video',
          data: `Animation created successfully. ID: ${result.animation_id}`,
          animationId: result.animation_id
        };
      } catch (error) {
        console.error('Error creating Manim animation:', error);
        return 'Error creating animation. Make sure the Manim service is running at http://localhost:8002';
      }
    },
    toModelOutput(result) {
      return {
        type: 'content',
        value:
          typeof result === 'string'
            ? [{ type: 'text', text: result }]
            : [{ type: 'text', text: `🎬 Mathematical Animation Created!\n\n${result.data}\n\nYou can view the animation by downloading it from: http://localhost:8002/download/${result.animationId}` }],
      };
    },
  });

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = await streamText({
    model: anthropic('claude-3-7-sonnet-20250219'),
    messages: convertToModelMessages(messages),
    system: `You are a helpful AI tutor specializing in mathematics. Your goal is to help guide the user through mathematical concepts and make them understand the actual concepts.

    Don't be overly agreeable, if the user is wrong point it out. Remember, you are a tutor, the user is a student.

    Keep the conversation friendly and engaging.

    Use the screenshot tool to see what the student is currently working on.

    IMPORTANT: When the user asks about mathematical concepts that can be visualized (functions, derivatives, integrals, Riemann sums, linear systems, etc.), ALWAYS use the createManimAnimation tool to generate a visual animation. This will help the student better understand the mathematical concepts through visual learning.

    Examples of when to use Manim animations:
    - Graphing functions (x^2, sin(x), etc.)
    - Showing derivatives with tangent lines
    - Visualizing integrals and area under curves
    - Demonstrating Riemann sums
    - Solving systems of linear equations
    - Displaying mathematical equations

    Always provide both the mathematical explanation AND create a visual animation to reinforce the learning.

`,
tools: {
    // getName,
    getCurrentImage: getUserPaper,
    createManimAnimation: createManimAnimation,
  },

    toolChoice: 'auto', // Enable automatic tool selection
    stopWhen: stepCountIs(3), // Enable multi-step tool execution (up to 3 steps)
  });

  return result.toUIMessageStreamResponse();
}
