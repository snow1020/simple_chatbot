// src/hooks/__tests__/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import useWebSocket from '../useWebSocket'; // Adjust path as necessary
import { io, Socket } from 'socket.io-client';

// Mock socket.io-client
// Define a type for our mock socket's event listeners
type EventCallback = (...args: any[]) => void;
interface MockSocketEventListeners {
  [event: string]: EventCallback | undefined;
}

// Create a mutable object for event listeners for the mock socket
let mockSocketEventListeners: MockSocketEventListeners = {};
const mockSocketId = 'mockSocketId123';

// The actual mock for the socket instance
const mockSocket = {
  on: jest.fn((event, callback) => {
    mockSocketEventListeners[event] = callback;
  }),
  onAny: jest.fn((callback) => { // Mock onAny for general message handling
    mockSocketEventListeners['*'] = callback; // Special key for onAny
  }),
  emit: jest.fn(),
  disconnect: jest.fn(),
  connect: jest.fn(), // Not typically called directly by useWebSocket, but good to have
  connected: false, // Initial state
  id: null as string | null, // Initial state
};

// Reset function for the mock socket state before each test
const resetMockSocket = () => {
  mockSocketEventListeners = {}; // Clear listeners
  mockSocket.on.mockClear();
  mockSocket.onAny.mockClear();
  mockSocket.emit.mockClear();
  mockSocket.disconnect.mockClear();
  mockSocket.connect.mockClear();
  mockSocket.connected = false;
  mockSocket.id = null;
};

// Mock the io function
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => mockSocket),
}));

// Helper function to simulate server emitting an event to the client
const simulateServerEvent = (event: string, ...args: any[]) => {
  const handler = mockSocketEventListeners[event];
  if (handler) {
    act(() => { // Wrap in act because it will cause state updates in the hook
      handler(...args);
    });
  }
  // For onAny
  const anyHandler = mockSocketEventListeners['*'];
  if (anyHandler) {
    act(() => {
        anyHandler(event, ...args);
    });
  }
};

const TEST_URL = 'ws://localhost:8000/test';

describe('useWebSocket Hook', () => {
  beforeEach(() => {
    resetMockSocket();
    // Reset the io mock itself if it's called multiple times across tests and needs fresh instances
    (io as jest.Mock).mockClear().mockReturnValue(mockSocket);
  });

  it('should initialize with "connecting" status and call io() with the URL', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    expect(result.current.status).toBe('connecting');
    expect(io).toHaveBeenCalledWith(TEST_URL, expect.any(Object)); // Check URL
  });

  it('should change status to "connected" when "connect" event is received', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    expect(result.current.status).toBe('connecting'); // Initial

    act(() => {
      mockSocket.connected = true; // Simulate connection property change
      mockSocket.id = mockSocketId;
    });
    simulateServerEvent('connect');

    expect(result.current.status).toBe('connected');
    expect(result.current.socket?.id).toBe(mockSocketId); // Check if socket instance in hook has id
  });

  it('should change status to "disconnected" when "disconnect" event is received', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    act(() => { // First connect
      mockSocket.connected = true;
      mockSocket.id = mockSocketId;
    });
    simulateServerEvent('connect');
    expect(result.current.status).toBe('connected');

    act(() => { // Then disconnect
      mockSocket.connected = false;
    });
    simulateServerEvent('disconnect', 'io server disconnect');
    expect(result.current.status).toBe('disconnected');
  });

  it('should change status to "error" when "connect_error" event is received', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    simulateServerEvent('connect_error', new Error('Connection failed'));
    expect(result.current.status).toBe('error');
  });

  it('should call onMessageReceived when a message is received via onAny', () => {
    const mockOnMessageReceived = jest.fn();
    renderHook(() => useWebSocket(TEST_URL, { onMessageReceived: mockOnMessageReceived }));

    const testEvent = 'test_message';
    const testData = { text: 'Hello from server' };
    simulateServerEvent(testEvent, testData);

    expect(mockOnMessageReceived).toHaveBeenCalledWith({ event: testEvent, data: testData });
  });

  it('should call onMessageReceived with multiple arguments correctly', () => {
    const mockOnMessageReceived = jest.fn();
    renderHook(() => useWebSocket(TEST_URL, { onMessageReceived: mockOnMessageReceived }));

    const testEvent = 'multi_arg_event';
    const arg1 = { text: 'Hello' };
    const arg2 = { type: 'greeting' };
    simulateServerEvent(testEvent, arg1, arg2);

    expect(mockOnMessageReceived).toHaveBeenCalledWith({ event: testEvent, data: [arg1, arg2] });
  });


  it('should call socket.emit when sendMessage is called and socket is connected', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    act(() => { // Connect first
      mockSocket.connected = true;
      mockSocket.id = mockSocketId;
    });
    simulateServerEvent('connect');

    const eventName = 'chat_message';
    const messagePayload = { text: 'Hello from client' };
    act(() => {
      result.current.sendMessage(eventName, messagePayload);
    });

    expect(mockSocket.emit).toHaveBeenCalledWith(eventName, messagePayload);
  });

  it('should not call socket.emit if sendMessage is called when socket is not connected', () => {
    const { result } = renderHook(() => useWebSocket(TEST_URL));
    // Do not simulate connect event, so socket.connected remains false (or whatever initial is)

    const eventName = 'chat_message';
    const messagePayload = { text: 'Hello from client' };
    act(() => {
      result.current.sendMessage(eventName, messagePayload);
    });

    expect(mockSocket.emit).not.toHaveBeenCalled();
  });

  it('should call socket.disconnect on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket(TEST_URL));

    // Ensure socket was set up
    act(() => {
      mockSocket.connected = true;
    });
    simulateServerEvent('connect');

    unmount();
    expect(mockSocket.disconnect).toHaveBeenCalledTimes(1);
  });

  it('should not try to connect if URL is initially empty or null', () => {
    renderHook(() => useWebSocket(''));
    expect(io).not.toHaveBeenCalled();

    (io as jest.Mock).mockClear(); // Clear previous calls

    renderHook(() => useWebSocket(null as any)); // Test with null
    expect(io).not.toHaveBeenCalled();
  });

  it('should re-establish connection if URL changes from empty to valid', () => {
    const { rerender } = renderHook(({ url }) => useWebSocket(url), { initialProps: { url: '' } });
    expect(io).not.toHaveBeenCalled();

    rerender({ url: TEST_URL });
    expect(io).toHaveBeenCalledWith(TEST_URL, expect.any(Object));
    // Further checks can be added for connection status if needed
  });
});
