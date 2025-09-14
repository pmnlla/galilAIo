import { useRef, useCallback, useState } from 'react';

interface ElevenLabsStreamingOptions {
  apiKey: string;
  voiceId?: string;
  model?: string;
  onAudioChunk?: (chunk: Uint8Array) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

interface AudioQueueItem {
  text: string;
  timestamp: number;
}

export function useElevenLabsStreaming({
  apiKey,
  voiceId = "21m00Tcm4TlvDq8ikWAM", // Default voice
  model = "eleven_turbo_v2_5",
  onAudioChunk,
  onError,
  onComplete
}: ElevenLabsStreamingOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioQueueItem[]>([]);
  const currentStreamRef = useRef<ReadableStreamDefaultReader | null>(null);
  const audioBufferRef = useRef<AudioBuffer[]>([]);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const initializeAudioContext = useCallback(async () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }
  }, []);

  const streamTextToSpeech = useCallback(async (text: string) => {
    if (!text.trim()) return;

    try {
      setIsStreaming(true);
      await initializeAudioContext();

      const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/' + voiceId + '/stream', {
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

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      currentStreamRef.current = reader;
      const audioChunks: Uint8Array[] = [];

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        audioChunks.push(value);
        onAudioChunk?.(value);
      }

      // Convert chunks to audio buffer and play
      const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
      const arrayBuffer = await audioBlob.arrayBuffer();
      
      if (audioContextRef.current) {
        const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
        audioBufferRef.current.push(audioBuffer);
        
        if (!isPlaying) {
          playNextAudioBuffer();
        }
      }

    } catch (error) {
      console.error('ElevenLabs streaming error:', error);
      onError?.(error as Error);
    } finally {
      setIsStreaming(false);
      currentStreamRef.current = null;
    }
  }, [apiKey, voiceId, model, onAudioChunk, onError, initializeAudioContext, isPlaying]);

  const playNextAudioBuffer = useCallback(() => {
    if (!audioContextRef.current || audioBufferRef.current.length === 0) {
      setIsPlaying(false);
      onComplete?.();
      return;
    }

    setIsPlaying(true);
    const audioBuffer = audioBufferRef.current.shift()!;
    const source = audioContextRef.current.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContextRef.current.destination);
    
    currentSourceRef.current = source;
    
    source.onended = () => {
      currentSourceRef.current = null;
      // Play next buffer if available
      setTimeout(() => playNextAudioBuffer(), 50); // Small delay between chunks
    };
    
    source.start();
  }, [onComplete]);

  const addTextToQueue = useCallback((text: string) => {
    // Add text to queue for processing
    audioQueueRef.current.push({
      text,
      timestamp: Date.now()
    });
  }, []);

  const processTextChunk = useCallback((chunk: string) => {
    // Process text chunk immediately for real-time streaming
    if (chunk.trim()) {
      streamTextToSpeech(chunk);
    }
  }, [streamTextToSpeech]);

  const stopAudio = useCallback(() => {
    // Stop current audio playback
    if (currentSourceRef.current) {
      currentSourceRef.current.stop();
      currentSourceRef.current = null;
    }
    
    // Stop streaming
    if (currentStreamRef.current) {
      currentStreamRef.current.cancel();
      currentStreamRef.current = null;
    }
    
    // Clear buffers
    audioBufferRef.current = [];
    audioQueueRef.current = [];
    
    setIsStreaming(false);
    setIsPlaying(false);
  }, []);

  const cleanup = useCallback(() => {
    stopAudio();
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, [stopAudio]);

  return {
    isStreaming,
    isPlaying,
    streamTextToSpeech,
    processTextChunk,
    addTextToQueue,
    stopAudio,
    cleanup
  };
}
