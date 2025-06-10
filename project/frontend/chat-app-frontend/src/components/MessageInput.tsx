import React, { useState } from 'react';

interface MessageInputProps {
  onSendMessage: (text: string) => void;
  isAiResponding: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, isAiResponding }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onSendMessage(text.trim());
      setText('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center p-2 sm:p-4 border-t bg-white">
      <input
        type="text"
        className="flex-grow p-2 sm:p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isAiResponding ? "AI is thinking..." : "Type a message..."}
        disabled={isAiResponding} // Optionally disable input field as well
      />
      <button
        type="submit"
        className={`p-2 sm:p-3 rounded-r-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors
                  ${isAiResponding ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600 text-white'}`}
        disabled={isAiResponding}
      >
        {isAiResponding ? (
          // Simple spinner
          <svg className="animate-spin h-5 w-5 text-white sm:hidden" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 sm:hidden">
            <path d="M3.105 3.105a1.5 1.5 0 012.09-.09l13.59 8.995a1.5 1.5 0 010 2.49L5.195 22.995a1.5 1.5 0 01-2.09-.09l-.095-.095a1.5 1.5 0 01.09-2.09L15.07 12 3.105 5.195a1.5 1.5 0 01-.09-2.09z" />
          </svg>
        )}
        <span className="hidden sm:inline">
          {isAiResponding ? 'Sending...' : 'Send'}
        </span>
      </button>
    </form>
  );
};

export default MessageInput;
