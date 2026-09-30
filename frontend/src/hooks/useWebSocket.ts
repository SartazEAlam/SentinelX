import { useEffect, useRef, useState } from 'react';
import { getWsUrl } from '../services/apiClient';
import type { WSMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (message: WSMessage) => void;
  reconnect?: boolean;
}

export function useWebSocket({ onMessage, reconnect = true }: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimeout: number;

    const connect = () => {
      try {
        const url = getWsUrl();
        const ws = new WebSocket(url);

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const data: WSMessage = JSON.parse(event.data);
            if (onMessage) {
              onMessage(data);
            }
          } catch (err) {
            console.error('Failed to parse WS message', err);
          }
        };

        ws.onerror = (e) => {
          console.error('WebSocket error:', e);
          setError(e);
        };

        ws.onclose = () => {
          setIsConnected(false);
          if (reconnect) {
            reconnectTimeout = window.setTimeout(connect, 5000);
          }
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('WebSocket setup error:', err);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [onMessage, reconnect]);

  return { isConnected, error, ws: wsRef.current };
}
