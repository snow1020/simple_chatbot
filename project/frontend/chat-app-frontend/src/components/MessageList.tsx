import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

interface MessageListProps {
  messages: Array<{ id: string; text: string; sender: 'user' | 'ai' }>;
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isScrolledToBottom = scrollHeight - clientHeight <= scrollTop + 100; // 100px threshold

      if (isScrolledToBottom) {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [messages]); // Dependency array includes messages

  // Add another useEffect for initial scroll to bottom when component mounts and messages are loaded
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  }, []); // Empty dependency array for initial mount, or [messages.length > 0] if you want to wait for first messages


  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col space-y-2 p-2 sm:p-4 h-full overflow-y-auto"
    >
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <div ref={messagesEndRef} /> {/* Invisible element to scroll to */}
    </div>
  );
};

export default MessageList;
