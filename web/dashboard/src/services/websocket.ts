import { io, Socket } from 'socket.io-client';

export interface WebSocketEvent {
  event: string;
  timestamp: string;
  data: any;
  metadata?: {
    session_id?: string;
    agent_name?: string;
    severity?: 'info' | 'warning' | 'error' | 'critical';
  };
}

export type EventCallback = (event: WebSocketEvent) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private eventCallbacks: Map<string, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnected = false;

  constructor() {
    // Initialize but don't connect immediately
  }

  connect(url: string = 'ws://localhost:8000/ws'): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      // Create WebSocket connection using native WebSocket
      // since Socket.IO isn't used on the backend
      this.setupNativeWebSocket(url);
      
      // Set up a timeout for connection
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 5000);

      // Wait for connection
      const checkConnection = setInterval(() => {
        if (this.isConnected) {
          clearInterval(checkConnection);
          clearTimeout(timeout);
          resolve();
        }
      }, 100);
    });
  }

  private setupNativeWebSocket(url: string) {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
      // Subscribe to all events by default
      this.sendMessage({
        action: 'subscribe',
        topic: 'all'
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleEvent(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.isConnected = false;
      this.handleReconnect(url);
    };

    // Store WebSocket reference
    (this as any).ws = ws;
  }

  private handleReconnect(url: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.setupNativeWebSocket(url);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.notifyConnectionLost();
    }
  }

  private handleEvent(event: WebSocketEvent) {
    // Handle special events
    if (event.event === 'connection.established') {
      console.log('Connection established:', event.data);
      this.notifyConnectionEstablished();
      return;
    }

    if (event.event === 'heartbeat') {
      // Update heartbeat status
      this.notifyHeartbeat(event.data);
      return;
    }

    // Notify all subscribers of this event type
    const callbacks = this.eventCallbacks.get(event.event);
    if (callbacks) {
      callbacks.forEach(callback => callback(event));
    }

    // Notify wildcard subscribers
    const wildcardCallbacks = this.eventCallbacks.get('*');
    if (wildcardCallbacks) {
      wildcardCallbacks.forEach(callback => callback(event));
    }
  }

  subscribe(eventType: string, callback: EventCallback): () => void {
    if (!this.eventCallbacks.has(eventType)) {
      this.eventCallbacks.set(eventType, new Set());
    }
    
    this.eventCallbacks.get(eventType)!.add(callback);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.eventCallbacks.get(eventType);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.eventCallbacks.delete(eventType);
        }
      }
    };
  }

  subscribeTo(topic: string) {
    this.sendMessage({
      action: 'subscribe',
      topic
    });
  }

  unsubscribeFrom(topic: string) {
    this.sendMessage({
      action: 'unsubscribe',
      topic
    });
  }

  sendMessage(message: any) {
    const ws = (this as any).ws as WebSocket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  ping() {
    this.sendMessage({
      action: 'ping'
    });
  }

  getRecentEvents(count: number = 50, eventType?: string): Promise<WebSocketEvent[]> {
    return new Promise((resolve) => {
      const messageId = Date.now().toString();
      
      // Set up one-time listener for response
      const unsubscribe = this.subscribe('recent_events', (event) => {
        if (event.data?.messageId === messageId) {
          unsubscribe();
          resolve(event.data.events || []);
        }
      });

      // Request recent events
      this.sendMessage({
        action: 'get_recent_events',
        count,
        event_type: eventType,
        messageId
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        unsubscribe();
        resolve([]);
      }, 5000);
    });
  }

  disconnect() {
    const ws = (this as any).ws as WebSocket;
    if (ws) {
      ws.close();
      (this as any).ws = null;
    }
    this.isConnected = false;
    this.eventCallbacks.clear();
  }

  isConnectedStatus(): boolean {
    return this.isConnected;
  }

  // Helper methods for specific event notifications
  private notifyConnectionEstablished() {
    const callbacks = this.eventCallbacks.get('connection.status');
    if (callbacks) {
      callbacks.forEach(callback => callback({
        event: 'connection.status',
        timestamp: new Date().toISOString(),
        data: { connected: true }
      }));
    }
  }

  private notifyConnectionLost() {
    const callbacks = this.eventCallbacks.get('connection.status');
    if (callbacks) {
      callbacks.forEach(callback => callback({
        event: 'connection.status',
        timestamp: new Date().toISOString(),
        data: { connected: false }
      }));
    }
  }

  private notifyHeartbeat(data: any) {
    const callbacks = this.eventCallbacks.get('heartbeat');
    if (callbacks) {
      callbacks.forEach(callback => callback({
        event: 'heartbeat',
        timestamp: new Date().toISOString(),
        data
      }));
    }
  }
}

// Export singleton instance
const websocketService = new WebSocketService();
export default websocketService;