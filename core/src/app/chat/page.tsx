'use client';

import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState, useRef, useCallback } from 'react';
import { useVoiceWebSocket } from '~/hooks/useVoiceWebSocket';

export default function Chat() {
  const { messages, sendMessage, status, stop } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/chat',
    }),
  });
  
  const [input, setInput] = useState('');
  const [voiceConnectionStatus, setVoiceConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const isGeneratingRef = useRef(false);

  // Update generation status tracking
  isGeneratingRef.current = status !== 'ready';

  const handleVoiceMessage = useCallback((text: string) => {
    // If currently generating a response, stop it first
    if (isGeneratingRef.current) {
      console.log('Interrupting ongoing generation for new voice input:', text);
      stop();
    }
    
    // Send the voice transcription as a message
    sendMessage({ text });
  }, [sendMessage, stop]);

  const handleVoiceConnectionChange = useCallback((connected: boolean) => {
    setVoiceConnectionStatus(connected ? 'connected' : 'disconnected');
  }, []);

  // Initialize voice WebSocket connection
  const { isConnected, connectionStatus } = useVoiceWebSocket({
    url: 'ws://127.0.0.1:8765',
    onMessage: handleVoiceMessage,
    onConnectionChange: handleVoiceConnectionChange,
  });

  return (
    <div className="flex flex-col w-full max-w-md py-24 mx-auto stretch">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-center flex-1">GalilAI Chat</h1>
        
        {/* Voice Connection Status */}
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
            connectionStatus === 'error' ? 'bg-red-500' :
            'bg-gray-400'
          }`}></div>
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? 'Voice Connected' :
             connectionStatus === 'connecting' ? 'Connecting...' :
             connectionStatus === 'error' ? 'Voice Error' :
             'Voice Disconnected'}
          </span>
        </div>
      </div>
      
      {/* Chat Messages */}
      <div className="space-y-4 mb-4 max-h-96 overflow-y-auto">
        {messages.map((message) => (
          <div key={message.id} className="whitespace-pre-wrap">
            <div className={`p-3 rounded-lg ${
              message.role === 'user' 
                ? 'bg-blue-100 ml-auto max-w-xs' 
                : 'bg-gray-100 mr-auto max-w-xs'
            }`}>
              <div className="text-xs font-semibold mb-1 capitalize">
                {message.role}
              </div>
              <div>
                {message.parts.map((part, index) => 
                  part.type === 'text' ? (
                    <span key={index}>{part.text}</span>
                  ) : null
                )}
              </div>
            </div>
          </div>
        ))}
        
        {status !== 'ready' && (
          <div className="bg-gray-100 mr-auto max-w-xs p-3 rounded-lg">
            <div className="text-xs font-semibold mb-1">Assistant</div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={(e) => {
        e.preventDefault();
        if (input.trim()) {
          sendMessage({ text: input });
          setInput('');
        }
      }} className="flex space-x-2">
        <input
          className="flex-1 p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={input}
          placeholder="Say something..."
          onChange={(e) => setInput(e.target.value)}
          disabled={status !== 'ready'}
        />
        <button
          type="submit"
          disabled={status !== 'ready'}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
        {status !== 'ready' && (
          <button
            type="button"
            onClick={stop}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
          >
            Stop
          </button>
        )}
      </form>
    </div>
  );
}
