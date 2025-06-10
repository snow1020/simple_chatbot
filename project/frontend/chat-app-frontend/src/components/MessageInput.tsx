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
    <form onSubmit={handleSubmit} className="flex items-center p-3 sm:p-4 border-t border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
      <input
        type="text"
        className="flex-grow p-3 border border-slate-300 dark:border-slate-600 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent bg-white dark:bg-slate-700 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isAiResponding ? "AI is thinking..." : "Type a message..."}
        disabled={isAiResponding}
      />
      <button
        type="submit"
        className={`p-3 rounded-r-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:ring-offset-1 dark:focus:ring-offset-slate-800 transition-colors
                  ${isAiResponding ? 'bg-slate-400 dark:bg-slate-600 cursor-not-allowed text-slate-600 dark:text-slate-400' : 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white'}`}
        disabled={isAiResponding}
      >
        {isAiResponding ? (
          <>
            <svg className="animate-spin h-5 w-5 text-white sm:hidden" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="hidden sm:inline">Sending...</span>
          </>
        ) : (
          <>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 sm:hidden">
              <path d="M3.105 3.105a1.5 1.5 0 012.09-.09l13.59 8.995a1.5 1.5 0 010 2.49L5.195 22.995a1.5 1.5 0 01-2.09-.09l-.095-.095a1.5 1.5 0 01.09-2.09L15.07 12 3.105 5.195a1.5 1.5 0 01-.09-2.09z" />
            </svg>
            <span className="hidden sm:inline">Send</span>
          </>
        )}
      </button>
    </form>
  );
};

export default MessageInput;
