import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center space-x-1 p-3 self-start">
      <div className="w-2.5 h-2.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
      <div className="w-2.5 h-2.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
      <div className="w-2.5 h-2.5 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce"></div>
      <span className="text-xs text-slate-500 dark:text-slate-400 ml-2">AI is typing...</span>
    </div>
  );
};

export default TypingIndicator;
