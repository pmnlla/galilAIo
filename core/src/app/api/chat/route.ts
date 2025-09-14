import { createAnthropic } from '@ai-sdk/anthropic';
import { streamText, convertToModelMessages, type UIMessage, stepCountIs, tool } from 'ai';
import { z } from 'zod';
import fs from 'node:fs';
import { spawn, type ChildProcessWithoutNullStreams } from 'child_process';
import { env } from '~/env';

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
  
  // Server-side TTS configuration
  const ttsEnabled = env.TTS_ENABLED;
  const elevenLabsApiKey = env.ELEVENLABS_API_KEY;
  const voiceId = env.ELEVENLABS_VOICE_ID;
  const model = env.ELEVENLABS_MODEL;
  
  console.log('TTS Config:', { ttsEnabled, hasApiKey: !!elevenLabsApiKey, voiceId, model });

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
      getCurrentImage: getUserPaper,
    },

    toolChoice: 'auto', // Enable automatic tool selection
    stopWhen: stepCountIs(3), // Enable multi-step tool execution (up to 3 steps)
    abortSignal: req.signal, // Forward abort signal for proper stop functionality
  });

  // If TTS is enabled, create a transform stream to intercept text chunks
  if (ttsEnabled && elevenLabsApiKey) {
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();
    
    let accumulatedText = '';
    let sentenceBuffer = '';
    let sseBuffer = '';
    const safeVoiceId = voiceId || '21m00Tcm4TlvDq8ikWAM';
    const safeModel = model || 'eleven_turbo_v2_5';
    // Narrowed by the if-guard above, safe to assert
    const safeApiKey = elevenLabsApiKey!;

    // Single ffplay process per response; merge sentence audio chunks
    type QueueItem = { type: 'text'; value: string } | { type: 'end' };
    const ttsQueue: QueueItem[] = [];
    let processingQueue = false;
    let ffplayProc: ChildProcessWithoutNullStreams | undefined;
    let ffplayClosePromise: Promise<void> | undefined;

    // Stop everything immediately (used for user interrupt / abort)
    async function stopTTS(reason: string) {
      try {
        console.log('TTS stop:', reason);
        // Clear any queued items and stop processing
        ttsQueue.length = 0;
        processingQueue = false;
        // End ffplay stdin to stop audio
        if (ffplayProc?.stdin && !ffplayProc.stdin.destroyed) {
          ffplayProc.stdin.end();
        }
        // Await process exit if available
        if (ffplayClosePromise) {
          await ffplayClosePromise.catch(() => {});
        }
      } finally {
        ffplayProc = undefined;
        ffplayClosePromise = undefined;
      }
    }

    // If the client cancels the HTTP request (e.g., user presses stop), abort TTS too
    try {
      // Next.js Request implements the Fetch API and provides a signal
      const abortSignal: AbortSignal | undefined = (req as any)?.signal;
      abortSignal?.addEventListener('abort', () => {
        stopTTS('request aborted by client').catch(err => console.error('TTS stop error:', err));
      });
    } catch {}

    async function startFfplay(): Promise<void> {
      if (ffplayProc) return;
      console.log('Starting ffplay process (merged stream)...');
      ffplayProc = spawn('ffplay', [
        '-f', 'mp3',
        '-i', 'pipe:0',
        '-autoexit',
        '-nodisp',
        '-loglevel', 'error',
      ]);
      ffplayProc.stderr?.on('data', (data: Buffer) => {
        console.log('ffplay stderr:', data.toString());
      });
      ffplayClosePromise = new Promise<void>((resolve, reject) => {
        ffplayProc!.on('error', (err: Error) => {
          console.error('Failed to start ffplay. Make sure FFmpeg is installed:', err);
          reject(err);
        });
        ffplayProc!.on('close', (code: number | null) => {
          console.log(`ffplay (merged) exited with code ${code}`);
          resolve();
        });
      });
    }

    async function streamElevenLabsToFfplay(text: string) {
      console.log('TTS merged queue item start:', text.substring(0, 60) + '...', 'remaining:', ttsQueue.length);
      const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${safeVoiceId}/stream`, {
        method: 'POST',
        headers: {
          'Accept': 'audio/mpeg',
          'Content-Type': 'application/json',
          'xi-api-key': safeApiKey,
        },
        body: JSON.stringify({
          text,
          model_id: safeModel,
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.8,
            style: 0.0,
            use_speaker_boost: true,
          },
        }),
      });
      console.log('ElevenLabs (merged) response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('ElevenLabs API error:', response.status, errorText);
        throw new Error(`ElevenLabs API error: ${response.status} - ${errorText}`);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Failed to get response reader');
      let total = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        total += value.length;
        if (ffplayProc?.stdin && !ffplayProc.stdin.destroyed) {
          ffplayProc.stdin.write(value);
        }
      }
      console.log(`Streamed ${total} bytes to ffplay (merged)`);
    }

    async function processQueue() {
      if (processingQueue) return;
      processingQueue = true;
      try {
        await startFfplay();
        while (ttsQueue.length > 0) {
          const item = ttsQueue.shift()!;
          if (item.type === 'text') {
            await streamElevenLabsToFfplay(item.value);
          } else if (item.type === 'end') {
            if (ffplayProc?.stdin && !ffplayProc.stdin.destroyed) {
              ffplayProc.stdin.end();
            }
            if (ffplayClosePromise) await ffplayClosePromise;
            ffplayProc = undefined;
            ffplayClosePromise = undefined;
          }
        }
      } catch (err) {
        console.error('TTS queue error:', err);
        // Ensure we try to close ffplay if something goes wrong
        if (ffplayProc?.stdin && !ffplayProc.stdin.destroyed) {
          ffplayProc.stdin.end();
        }
        if (ffplayClosePromise) await ffplayClosePromise.catch(() => {});
        ffplayProc = undefined;
        ffplayClosePromise = undefined;
      } finally {
        processingQueue = false;
      }
    }

    function enqueueTTS(text: string) {
      ttsQueue.push({ type: 'text', value: text });
      processQueue().catch(err => console.error('TTS queue error:', err));
    }
    function enqueueEnd() {
      ttsQueue.push({ type: 'end' });
      processQueue().catch(err => console.error('TTS queue error:', err));
    }
    
    const ttsTransformStream = new TransformStream({
      transform(chunk, controller) {
        // Forward the original chunk to the UI
        controller.enqueue(chunk);
        
        // Extract text content for TTS processing using SSE (data stream protocol)
        const chunkStr = decoder.decode(chunk);
        sseBuffer += chunkStr;

        // Process complete SSE events separated by blank lines
        let sepIndex: number;
        while ((sepIndex = sseBuffer.indexOf('\n\n')) !== -1) {
          const eventBlock = sseBuffer.slice(0, sepIndex);
          sseBuffer = sseBuffer.slice(sepIndex + 2);

          // Ignore comment/ping lines starting with ':'
          const lines = eventBlock.split('\n').filter(l => l.trim().length > 0 && !l.startsWith(':'));
          // Handle [DONE]
          if (lines.some(l => l.includes('[DONE]'))) {
            if (sentenceBuffer.trim()) {
              console.log('Queueing final text to TTS (DONE):', sentenceBuffer.trim().substring(0, 50) + '...');
              enqueueTTS(sentenceBuffer.trim());
              sentenceBuffer = '';
            }
            // Signal end of merged stream
            enqueueEnd();
            continue;
          }

          // Collect data payload lines (SSE can have multiple data: lines)
          const dataPayloadLines = lines
            .filter(l => l.startsWith('data:'))
            .map(l => l.replace(/^data:\s?/, ''));
          if (dataPayloadLines.length === 0) continue;

          const dataPayload = dataPayloadLines.join('\n');
          try {
            const data = JSON.parse(dataPayload);
            const t = data.type as string | undefined;
            if (!t) continue;

            // Log a small trace for debugging
            if (t.startsWith('text') || t === 'finish') {
              const deltaPreview = typeof data.delta === 'string' ? data.delta.substring(0, 30) : '';
              console.log('SSE part:', t, deltaPreview ? `"${deltaPreview}"` : '');
            }

            // Handle text stream parts per AI SDK docs
            if (t === 'text-delta' && typeof data.delta === 'string') {
              const piece = data.delta as string;
              sentenceBuffer += piece;
              accumulatedText += piece;

              // Detect and send complete sentences
              const sentences = sentenceBuffer.match(/[^.!?]*[.!?]/g);
              if (sentences) {
                for (const sentence of sentences) {
                  if (sentence.trim()) {
                    console.log('Queueing for TTS:', sentence.trim().substring(0, 50) + '...');
                    enqueueTTS(sentence.trim());
                  }
                }
                // Keep remaining incomplete sentence
                sentenceBuffer = sentenceBuffer.replace(/[^.!?]*[.!?]/g, '');
              }
            }

            // Flush any remaining text on finish
            if (t === 'finish') {
              if (sentenceBuffer.trim()) {
                console.log('Queueing final text to TTS:', sentenceBuffer.trim().substring(0, 50) + '...');
                enqueueTTS(sentenceBuffer.trim());
                sentenceBuffer = '';
              }
              // Signal end of merged stream
              enqueueEnd();
            }
          } catch (e) {
            // Ignore JSON parse errors for any non-JSON data lines
          }
        }
      }
    });

    // Create the response with TTS transform
    const response = result.toUIMessageStreamResponse();
    const transformedStream = response.body?.pipeThrough(ttsTransformStream);
    
    return new Response(transformedStream, {
      headers: response.headers,
      status: response.status,
    });
  }

  return result.toUIMessageStreamResponse();
}

// Helper function to send text to ElevenLabs and play with ffplay
async function sendToElevenLabs(text: string, apiKey: string, voiceId: string, model: string) {
  console.log('sendToElevenLabs called with:', { text: text.substring(0, 30), hasApiKey: !!apiKey, voiceId, model });
  
  if (!apiKey) {
    console.error('No ElevenLabs API key provided');
    return;
  }
  
  try {
    console.log('Making request to ElevenLabs...');
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream`, {
      method: 'POST',
      headers: {
        'Accept': 'audio/mpeg',
        'Content-Type': 'application/json',
        'xi-api-key': apiKey,
      },
      body: JSON.stringify({
        text: text,
        model_id: model,
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.8,
          style: 0.0,
          use_speaker_boost: true
        }
      }),
    });

    console.log('ElevenLabs response status:', response.status);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('ElevenLabs API error:', response.status, errorText);
      throw new Error(`ElevenLabs API error: ${response.status} - ${errorText}`);
    }

    // Initialize ffplay process
    let ffplay: ChildProcessWithoutNullStreams | undefined;
    try {
      console.log('Starting ffplay process...');
      ffplay = spawn('ffplay', [
        '-f', 'mp3',  // Specify input format
        '-i', 'pipe:0',
        '-autoexit',
        '-nodisp',  // No video display
        '-loglevel', 'error'  // Show errors but not info
      ]);
      
      // Create a promise we can await to ensure serialization
      const ffplayClosePromise = new Promise<void>((resolve, reject) => {
        ffplay!.on('error', (err: Error) => {
          console.error('Failed to start ffplay. Make sure FFmpeg is installed:', err);
          reject(err);
        });
        ffplay!.on('close', (code: number | null) => {
          console.log(`ffplay process exited with code ${code}`);
          resolve();
        });
      });
      
      ffplay.stderr?.on('data', (data: Buffer) => {
        console.log('ffplay stderr:', data.toString());
      });

      // Stream audio data to ffplay
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      let totalBytes = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          totalBytes += value.length;
          if (ffplay?.stdin && !ffplay.stdin.destroyed) {
            ffplay.stdin.write(value);
          }
        }
        console.log(`Streamed ${totalBytes} bytes to ffplay`);
        if (ffplay?.stdin && !ffplay.stdin.destroyed) {
          ffplay.stdin.end();
        }
        console.log(`TTS audio played for: "${text.substring(0, 50)}..."`);
      } catch (streamError) {
        console.error('Error streaming audio to ffplay:', streamError);
        if (ffplay?.stdin && !ffplay.stdin.destroyed) {
          ffplay.stdin.end();
        }
      }

      // Await process exit to serialize next playback
      await ffplayClosePromise;

    } catch (error) {
      console.error('Failed to initialize ffplay:', error);
      return;
    }
  } catch (error) {
    console.error('ElevenLabs TTS error:', error);
  }
}
