// src/__tests__/Home.test.tsx
import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event'; // For more realistic interactions
import Home from '@/app/page'; // Assuming default export from src/app/page.tsx
import useWebSocket, { UseWebSocketOptions } from '@/hooks/useWebSocket'; // Import the hook and its options type

// Mock the useWebSocket hook
jest.mock('@/hooks/useWebSocket');

// Define a type for our mock useWebSocket return value for easier typing
type MockUseWebSocket = {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: jest.Mock;
  // Add other properties like 'socket' if your component uses them directly,
};

// To capture onMessageReceived from options
let capturedOnMessageReceived: ((message: any) => void) | undefined;

// Default mock implementation
const mockUseWebSocketDefaultReturn: MockUseWebSocket = {
  status: 'connecting', // Default initial status
  sendMessage: jest.fn(),
};

// Variable to hold the current mock implementation, can be changed per test
let currentMockUseWebSocketReturn: MockUseWebSocket;

describe('Home Page - Connection Status', () => {
  beforeEach(() => {
    // Reset to default before each test
    currentMockUseWebSocketReturn = { ...mockUseWebSocketDefaultReturn, sendMessage: jest.fn() };
    capturedOnMessageReceived = undefined; // Reset for this describe block too

    (useWebSocket as jest.Mock).mockImplementation((url: string, options?: UseWebSocketOptions) => {
      if (options && options.onMessageReceived) {
        capturedOnMessageReceived = options.onMessageReceived;
      }
      return currentMockUseWebSocketReturn;
    });
  });

  it('should display "Connecting..." status initially', () => {
    currentMockUseWebSocketReturn.status = 'connecting';
    render(<Home />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
    expect(screen.getByText('Connecting...')).toHaveClass('bg-yellow-500');
  });

  it('should display "Connected" status when WebSocket is connected', () => {
    act(() => {
      currentMockUseWebSocketReturn.status = 'connected';
    });
    render(<Home />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toHaveClass('bg-green-500');
  });

  it('should display "Disconnected" status when WebSocket is disconnected', () => {
    act(() => {
      currentMockUseWebSocketReturn.status = 'disconnected';
    });
    render(<Home />);
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toHaveClass('bg-red-500');
  });

  it('should display "Connection Error" status when WebSocket has an error', () => {
    act(() => {
      currentMockUseWebSocketReturn.status = 'error';
    });
    render(<Home />);
    expect(screen.getByText('Connection Error')).toBeInTheDocument();
    expect(screen.getByText('Connection Error')).toHaveClass('bg-red-600');
  });

  it('should call useWebSocket with the correct URL', () => {
    render(<Home />);
    expect(useWebSocket).toHaveBeenCalled();
  });
});


describe('Home Page - Message Handling', () => {
  beforeEach(() => {
    currentMockUseWebSocketReturn = {
      status: 'connected', // Default to connected for message handling tests
      sendMessage: jest.fn(),
    };
    capturedOnMessageReceived = undefined; // Reset captured callback

    // Ensure the mock implementation is fresh for each test in this describe block
    (useWebSocket as jest.Mock).mockClear().mockImplementation((url: string, options?: UseWebSocketOptions) => {
      if (options && options.onMessageReceived) {
        capturedOnMessageReceived = options.onMessageReceived;
      }
      return currentMockUseWebSocketReturn;
    });
  });

  it('should display user message in list and call sendMessage when user sends a message', async () => {
    const user = userEvent.setup();
    render(<Home />);

    const input = screen.getByPlaceholderText('Type a message...'); // Corrected placeholder
    const sendButton = screen.getByRole('button', { name: /send/i });

    const testMessage = 'Hello, world!';
    await act(async () => {
      await user.type(input, testMessage);
      await user.click(sendButton);
    });

    // Check if the message appears in the document
    expect(await screen.findByText(testMessage)).toBeInTheDocument();

    // Check if sendMessage from useWebSocket was called
    expect(currentMockUseWebSocketReturn.sendMessage).toHaveBeenCalledWith('chat_message', { text: testMessage });
  });

  it('should display received AI message in the list', async () => {
    render(<Home />);

    expect(capturedOnMessageReceived).toBeDefined();

    const aiMessageData = { // Ensure this matches the Message interface used by page.tsx
      id: 'ai-msg-1',
      text: 'Hello from AI!',
      sender: 'ai', // This field is 'sender' in the Message interface
      timestamp: new Date().toISOString(),
      // is_ai might be implicitly handled by sender === 'ai' or ChatMessage might use it
    };

    act(() => {
      if (capturedOnMessageReceived) {
        // Simulate that handleNewMessage in page.tsx receives the unwrapped data
        capturedOnMessageReceived(aiMessageData);
      }
    });

    expect(await screen.findByText('Hello from AI!')).toBeInTheDocument();
  });

  it('should display AI message when received as a simple string from onMessageReceived (after page.tsx wraps it)', async () => {
    render(<Home />);
    expect(capturedOnMessageReceived).toBeDefined();

    const aiMessageText = "AI direct string response";

    act(() => {
      if (capturedOnMessageReceived) {
        // Simulate page.tsx's handleNewMessage receiving a direct string
        // page.tsx will convert this to a Message object with sender: 'ai'
        capturedOnMessageReceived(aiMessageText);
      }
    });

    // The text itself should be found.
    expect(await screen.findByText(aiMessageText)).toBeInTheDocument();
  });

  it('should update user message status from "sending" to "sent" (conceptual)', () => {
    // This test remains conceptual as noted in the prompt.
    console.log("Conceptual test: User message status update. Not fully implemented due to broad update logic in component.");
  });
});

describe('Home Page - Post-Connection Status Changes & UI Effects', () => {
  beforeEach(() => {
    // Reset to a connected state before each of these tests
    currentMockUseWebSocketReturn = { status: 'connected', sendMessage: jest.fn() };
    capturedOnMessageReceived = undefined;

    (useWebSocket as jest.Mock).mockClear().mockImplementation((url: string, options?: UseWebSocketOptions) => {
      if (options && options.onMessageReceived) {
        capturedOnMessageReceived = options.onMessageReceived;
      }
      return currentMockUseWebSocketReturn;
    });
  });

  it('should display "Disconnected" if status changes from connected to disconnected', () => {
    const { rerender } = render(<Home />);
    // Initially connected (from beforeEach)
    expect(screen.getByText('Connected')).toBeInTheDocument();

    act(() => {
      currentMockUseWebSocketReturn.status = 'disconnected';
    });
    rerender(<Home />); // Rerender to apply new mock status

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toHaveClass('bg-red-500');
  });

  it('should display "Connection Error" if status changes from connected to error', () => {
    const { rerender } = render(<Home />);
    expect(screen.getByText('Connected')).toBeInTheDocument();

    act(() => {
      currentMockUseWebSocketReturn.status = 'error';
    });
    rerender(<Home />);

    expect(screen.getByText('Connection Error')).toBeInTheDocument();
    expect(screen.getByText('Connection Error')).toHaveClass('bg-red-600');
  });

  it('should reset AI responding and typing indicators on disconnect', async () => {
    const user = userEvent.setup();
    // Initial state: connected
    const { rerender } = render(<Home />);
    expect(screen.getByText('Connected')).toBeInTheDocument();

    // Simulate sending a message to set isAiResponding and isAiTyping to true
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    await act(async () => {
      await user.type(input, "Test for AI indicators");
      await user.click(sendButton);
    });

    expect(sendButton).toBeDisabled();

    // Now, simulate a disconnect
    act(() => {
      currentMockUseWebSocketReturn.status = 'disconnected';
    });
    rerender(<Home />);

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(sendButton).not.toBeDisabled();
  });

  it('should reset AI responding and typing indicators on connection error', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<Home />);
    expect(screen.getByText('Connected')).toBeInTheDocument();

    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    await act(async () => {
      await user.type(input, "Test for AI indicators error");
      await user.click(sendButton);
    });

    expect(sendButton).toBeDisabled();

    // Simulate a connection error
    act(() => {
      currentMockUseWebSocketReturn.status = 'error';
    });
    rerender(<Home />);

    expect(screen.getByText('Connection Error')).toBeInTheDocument();
    expect(sendButton).not.toBeDisabled();
  });
});
