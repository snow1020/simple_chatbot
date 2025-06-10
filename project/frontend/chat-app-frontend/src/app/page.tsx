"use client";

import React, { useState, useEffect, useCallback } from 'react';
import MessageList from '@/components/MessageList';
import MessageInput from '@/components/MessageInput';
import useWebSocket from '@/hooks/useWebSocket'; // Import the hook

// Define the message type
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
}

// Define the WebSocket server URL
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws/chat';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isAiResponding, setIsAiResponding] = useState(false);

  const handleMessageReceived = useCallback((msg: any) => {
    setIsAiResponding(false); // AI has responded
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
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setIsAiResponding(true); // Set AI responding status before sending

    // Send the message to the WebSocket server
    // The backend should be set up to listen for a 'chat_message' event (or similar)
    sendMessage('chat_message', { text });
    // The backend is expected to broadcast this message or send an AI response
  };

  // It might also be prudent to set isAiResponding to false if the websocket disconnects or errors out
  // while waiting for a response.
  useEffect(() => {
    if (status === 'disconnected' || status === 'error') {
      setIsAiResponding(false);
    }
  }, [status]);

  useEffect(() => {
    // Log connection status changes
    console.log('WebSocket Connection Status:', status);
  }, [status]);

  const ConnectionStatusDisplay = () => {
    let text = '';
    let colorClass = '';

    switch (status) {
      case 'connecting':
        text = 'Connecting...';
        colorClass = 'text-yellow-300';
        break;
      case 'connected':
        text = 'Connected';
        colorClass = 'text-green-300';
        break;
      case 'disconnected':
        text = 'Disconnected';
        colorClass = 'text-red-300';
        break;
      case 'error':
        text = 'Connection Error';
        colorClass = 'text-red-400';
        break;
      default:
        text = 'Unknown Status';
        colorClass = 'text-gray-300';
    }
    return <p className={`text-sm ${colorClass}`}>{text}</p>;
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-3 sm:p-4 text-center shadow-md">
        <h1 className="text-lg sm:text-xl font-semibold">Chat App</h1>
        <ConnectionStatusDisplay />
      </header>
      {/* The main chat area will take up the remaining height and allow internal scrolling for messages */}
      <main className="flex-grow flex flex-col overflow-hidden">
        {/* MessageList container: flex-grow to take space, overflow-y-auto for scrolling messages */}
        <div className="flex-grow overflow-y-auto"> {/* Removed p-4, MessageList now handles its internal padding */}
          <MessageList messages={messages} />
        </div>
        {/* MessageInput is fixed at the bottom */}
        <MessageInput onSendMessage={handleSendMessage} isAiResponding={isAiResponding} />
      </main>
    </div>
  );
}
