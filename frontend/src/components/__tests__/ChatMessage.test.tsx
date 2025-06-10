// src/components/__tests__/ChatMessage.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import ChatMessage from '../ChatMessage'; // Adjust path if necessary
import { Message } from '@/app/page'; // Assuming Message type is exported from page.tsx or a types file

// If Message type is not exported, define it locally for the test:
// interface Message {
//   id: string;
//   text: string;
//   sender: 'user' | 'ai';
//   status?: 'sending' | 'sent' | 'failed';
// }

describe('ChatMessage Component', () => {
  it('should render user message text correctly', () => {
    const userMessage: Message = {
      id: 'user-msg-1',
      text: 'Hello from user',
      sender: 'user',
    };
    render(<ChatMessage message={userMessage} />);
    expect(screen.getByText('Hello from user')).toBeInTheDocument();
    // Check for user-specific class to be thorough
    expect(screen.getByText('Hello from user').parentElement).toHaveClass('bg-sky-500');
  });

  it('should render AI message text correctly', () => {
    const aiMessage: Message = {
      id: 'ai-msg-1',
      text: 'Hello from AI test',
      sender: 'ai',
    };
    render(<ChatMessage message={aiMessage} />);
    // This is the crucial assertion
    expect(screen.getByText('Hello from AI test')).toBeInTheDocument();
    // Check for AI-specific class
    expect(screen.getByText('Hello from AI test').parentElement).toHaveClass('bg-slate-200');
  });

  it('should display "Sending..." status for user messages when status is "sending"', () => {
    const userMessageSending: Message = {
      id: 'user-msg-2',
      text: 'User message sending',
      sender: 'user',
      status: 'sending',
    };
    render(<ChatMessage message={userMessageSending} />);
    expect(screen.getByText('User message sending')).toBeInTheDocument();
    expect(screen.getByText('Sending...')).toBeInTheDocument();
  });

  it('should not display "Sending..." status for AI messages even if status is "sending"', () => {
    const aiMessageSending: Message = {
      id: 'ai-msg-2',
      text: 'AI message with sending status',
      sender: 'ai',
      status: 'sending', // AI messages shouldn't show this
    };
    render(<ChatMessage message={aiMessageSending} />);
    expect(screen.getByText('AI message with sending status')).toBeInTheDocument();
    expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
  });
});
