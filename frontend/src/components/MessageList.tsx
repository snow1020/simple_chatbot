import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import TypingIndicator from './TypingIndicator'; // Import the TypingIndicator

interface MessageListProps {
  messages: Array<{ id: string; text: string; sender: 'user' | 'ai' }>;
  isAiTyping?: boolean; // Add isAiTyping to props
}

const MessageList: React.FC<MessageListProps> = ({ messages, isAiTyping }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      // Check if the user is scrolled near the bottom, or if it's the initial load (scrollTop typically 0)
      // Add a larger threshold to ensure it scrolls even if the user is slightly scrolled up.
      const isScrolledToBottom = scrollHeight - clientHeight <= scrollTop + 200; // Increased threshold to 200px

      if (isScrolledToBottom) {
        // Using block: 'end' to ensure it scrolls to the very bottom of the target.
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }
    // Adding isAiTyping to the dependency array to trigger scroll when typing indicator appears/disappears
  }, [messages, isAiTyping]);

  // Initial scroll to bottom on mount. 'auto' behavior is fine for initial load.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' });
  }, []);


  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col space-y-4 p-4 h-full overflow-y-auto" // Styles for overall list container
    >
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      {/* The TypingIndicator is part of the scrollable content */}
      {isAiTyping && (
        <div className="self-start"> {/* Ensure typing indicator aligns left like AI messages */}
          <TypingIndicator />
        </div>
      )}
      {/* This div is the target for scrolling to the bottom */}
      <div ref={messagesEndRef} className="h-0" /> {/* Making it zero height as it's just a scroll target */}
    </div>
  );
};

export default MessageList;
