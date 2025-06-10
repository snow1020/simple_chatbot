import React from 'react';

interface ChatMessageProps {
  message: { id: string; text: string; sender: 'user' | 'ai' };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const userMessageClasses = 'bg-blue-500 text-white self-end ml-auto';
  const aiMessageClasses = 'bg-gray-300 text-black self-start mr-auto';
  const messageClass = message.sender === 'user' ? userMessageClasses : aiMessageClasses;

  return (
    <div
      className={`p-2 sm:p-3 rounded-lg shadow-sm max-w-[75%] sm:max-w-[70%] md:max-w-[60%] break-words ${messageClass}`}
    >
      {message.text}
    </div>
  );
};

export default ChatMessage;
