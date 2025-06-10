import React from 'react';

interface ChatMessageProps {
  message: {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    status?: 'sending' | 'sent' | 'failed'; // Include status in props
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  // Define base classes for all messages
  const baseMessageClasses = 'p-3 rounded-xl shadow-md max-w-[75%] sm:max-w-[70%] break-words transition-all duration-150 ease-in-out relative'; // Added relative for positioning status

  // Define classes specific to user messages
  const userMessageClasses = `bg-sky-500 hover:bg-sky-600 text-white self-end ml-auto dark:bg-sky-600 dark:hover:bg-sky-700`;

  // Define classes specific to AI messages
  const aiMessageClasses = `bg-slate-200 hover:bg-slate-300 text-slate-800 self-start mr-auto dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100`;

  // Combine base classes with sender-specific classes
  const messageClass = `${baseMessageClasses} ${message.sender === 'user' ? userMessageClasses : aiMessageClasses}`;

  return (
    <div className={messageClass}>
      <div>{message.text}</div>
      {message.sender === 'user' && message.status === 'sending' && (
        <div className="text-xs text-slate-200 dark:text-sky-300 italic pt-1 text-right">
          Sending...
        </div>
      )}
      {/* Placeholder for 'failed' status if needed later */}
      {/* {message.sender === 'user' && message.status === 'failed' && (
        <div className="text-xs text-red-300 dark:text-red-400 italic pt-1 text-right">
          Failed
        </div>
      )} */}
    </div>
  );
};

export default ChatMessage;
