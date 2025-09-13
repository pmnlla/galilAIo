import { ollama } from 'ollama-ai-provider-v2';
import { streamText, convertToModelMessages, type UIMessage } from 'ai';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = await streamText({
    model: ollama('gemma3:4b'), 
    messages: convertToModelMessages(messages),
    system: `You are a helpful AI assistant. You can help with various tasks including:
- Answering questions
- Writing and editing text
- Coding assistance
- Analysis and research
- Creative tasks

Be concise, helpful, and accurate in your responses.`,
  });

  return result.toUIMessageStreamResponse();
}
