"use client";

import React, { useState, useEffect, useCallback } from 'react';
import MessageList from '@/components/MessageList';
import MessageInput from '@/components/MessageInput';
import useWebSocket from '@/hooks/useWebSocket'; // Import the hook

// Define the message type
export interface Message { // Add export
  id: string;
  text: string;
  sender: 'user' | 'ai';
  status?: 'sending' | 'sent' | 'failed'; // New status field for user messages
}

// Define the WebSocket server URL
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAiResponding, setIsAiResponding] = useState(false);
  const [isAiTyping, setIsAiTyping] = useState(false); // New state for AI typing

  const handleMessageReceived = useCallback((msg: any) => {
    setIsAiResponding(false); // AI has responded
    setIsAiTyping(false); // AI has finished typing

    // Update status of 'sending' messages to 'sent'
    // This is a simplification for this subtask. Ideally, server acks would update specific messages.
    setMessages(prevMessages =>
      prevMessages.map(m => (m.status === 'sending' ? { ...m, status: 'sent' } : m))
    );

    console.log('Message received from server:', msg);
    // Assuming the server sends messages in a format that can be directly used
    // or needs transformation. For socket.io, msg might be { event: string, data: any }
    // We expect the backend to send a message structured like our Message interface,
    // or an object that contains the text and identifies the sender as 'ai'.

    // Example: if server sends { text: "Hello from AI", sender: "ai" } on 'chat_message' event
    if (msg.event === 'chat_message' && msg.data && msg.data.text) {
      const aiMessage: Message = {
        id: Date.now().toString() + '-ai', // Simple ID generation
        text: msg.data.text,
        sender: 'ai', // Or determine sender based on msg.data.sender if provided
      };
      setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } else if (typeof msg === 'string') { // Handle plain string messages if server sends that
        const aiMessage: Message = {
            id: Date.now().toString() + '-ai',
            text: msg,
            sender: 'ai',
        };
        setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } else if (msg.text && msg.sender) { // Handle object messages if server sends that
        const aiMessage: Message = {
            id: Date.now().toString() + '-ai',
            text: msg.text,
            sender: msg.sender,
        };
        setMessages((prevMessages) => [...prevMessages, aiMessage]);
    }
    // Add more conditions if the server message format varies
  }, []);

  const { status, sendMessage } = useWebSocket(WEBSOCKET_URL, {
    onMessageReceived: handleMessageReceived,
    // Potential: Add onError callback from useWebSocket if it signals specific message processing errors
  });

  const handleSendMessage = (text: string) => {
    const newMessageId = Date.now().toString(); // Generate ID once
    const newMessage: Message = {
      id: newMessageId,
      text,
      sender: 'user',
      status: 'sending', // Set initial status to 'sending'
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setIsAiResponding(true); // Set AI responding status before sending

    // Send the message to the WebSocket server
    // The backend should be set up to listen for a 'chat_message' event (or similar)
    sendMessage('chat_message', { text });
    setIsAiTyping(true); // Assume AI starts typing immediately after user sends a message
    // The backend is expected to broadcast this message or send an AI response
  };

  // It might also be prudent to set isAiResponding to false if the websocket disconnects or errors out
  // while waiting for a response.
  useEffect(() => {
    if (status === 'disconnected' || status === 'error') {
      setIsAiResponding(false);
      setIsAiTyping(false); // Stop typing indicator if connection issues
    }
  }, [status]);

  useEffect(() => {
    // Log connection status changes
    console.log('WebSocket Connection Status:', status);
  }, [status]);

  const ConnectionStatusDisplay = () => {
    let text = '';
    let baseClasses = 'text-xs px-2 py-0.5 rounded-full'; // Base classes for the status badge
    let colorClass = '';

    switch (status) {
      case 'connecting':
        text = 'Connecting...';
        colorClass = 'bg-yellow-500 text-yellow-900'; // Darker text for better contrast on yellow
        break;
      case 'connected':
        text = 'Connected';
        colorClass = 'bg-green-500 text-green-900'; // Darker text for better contrast on green
        break;
      case 'disconnected':
        text = 'Disconnected';
        colorClass = 'bg-red-500 text-white';
        break;
      case 'error':
        text = 'Connection Error';
        colorClass = 'bg-red-600 text-white';
        break;
      default:
        text = 'Unknown';
        colorClass = 'bg-gray-500 text-white';
    }
    // For 'Connecting...' and 'Connected', we might want a slightly different presentation,
    // maybe not a full badge but subtle text. This is an example of a badge style.
    return <p className={`inline-block ${baseClasses} ${colorClass}`}>{text}</p>;
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100 dark:bg-slate-900">
      <header className="bg-indigo-700 dark:bg-indigo-900 text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Chatterbox</h1>
          <ConnectionStatusDisplay />
        </div>
      </header>
      {/* The main chat area will take up the remaining height and allow internal scrolling for messages */}
      <main className="flex-grow flex flex-col overflow-hidden container mx-auto w-full max-w-4xl">
        {/* MessageList container: flex-grow to take space, overflow-y-auto for scrolling messages */}
        <div className="flex-grow overflow-y-auto">
          <MessageList messages={messages} isAiTyping={isAiTyping} />
        </div>
        {/* MessageInput is fixed at the bottom */}
        <MessageInput onSendMessage={handleSendMessage} isAiResponding={isAiResponding} />
      </main>
    </div>
  );
}
