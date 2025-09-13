'use client';

import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';

export default function Chat() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/chat',
    }),
  });
  
  const [input, setInput] = useState('');

  return (
    <div className="flex flex-col w-full max-w-md py-24 mx-auto stretch">
      <h1 className="text-2xl font-bold mb-6 text-center">GalilAI Chat</h1>
      
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
      </form>
    </div>
  );
}
