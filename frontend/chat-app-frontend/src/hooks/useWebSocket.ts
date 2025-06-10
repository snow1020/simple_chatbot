import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  onMessageReceived?: (message: any) => void; // Can be more specific with message type
}

interface UseWebSocketReturn {
  socket: Socket | null;
  status: WebSocketStatus;
  sendMessage: (event: string, message: any) => void;
}

const useWebSocket = (url: string, options?: UseWebSocketOptions): UseWebSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const { onMessageReceived } = options || {};

  useEffect(() => {
    if (!url) return;

    if (typeof window === 'undefined') {
      return;
    }

    setStatus('connecting');
    const newSocket = io(url, {
      // Consider adding common socket.io options if needed
      // e.g., transports: ['websocket']
    });

    newSocket.on('connect', () => {
      setStatus('connected');
      console.log('WebSocket connected:', newSocket.id);
    });

    newSocket.on('disconnect', (reason) => {
      setStatus('disconnected');
      console.log('WebSocket disconnected:', reason);
    });

    newSocket.on('connect_error', (error) => {
      setStatus('error');
      console.error('WebSocket connection error:', error);
    });

    // General message handler
    if (onMessageReceived) {
      // Assuming the server might emit various events, or a generic 'message' event
      // For a chat app, you might listen to a specific event like 'chat_message'
      newSocket.onAny((event, ...args) => {
        // console.log(`Received event: ${event}`, args);
        onMessageReceived({ event, data: args.length > 1 ? args : args[0] });
      });
    }

    setSocket(newSocket);

    return () => {
      console.log('Closing WebSocket connection');
      newSocket.disconnect();
      setSocket(null);
      setStatus('disconnected');
    };
  }, [url, onMessageReceived]); // onMessageReceived is a dependency

  const sendMessage = useCallback((event: string, message: any) => {
    if (socket && socket.connected) {
      socket.emit(event, message);
      // console.log(`Sent message on event ${event}:`, message);
    } else {
      console.error('WebSocket is not connected. Cannot send message.');
    }
  }, [socket]);

  return { socket, status, sendMessage };
};

export default useWebSocket;
