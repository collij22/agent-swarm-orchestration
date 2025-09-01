import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { GameState, WebSocketMessage, ChatMessage, GameMove } from '../api/types';
import { apiClient } from '../api/client';
import { useAuth } from './AuthContext';

interface GameContextType {
  currentGame: GameState | null;
  isConnected: boolean;
  chatMessages: ChatMessage[];
  joinGame: (gameId: string) => Promise<void>;
  leaveGame: () => void;
  makeMove: (move: Omit<GameMove, 'gameId'>) => Promise<void>;
  sendChatMessage: (message: string) => void;
  isLoading: boolean;
  error: string | null;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const useGame = () => {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

interface GameProviderProps {
  children: ReactNode;
}

export const GameProvider: React.FC<GameProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [currentGame, setCurrentGame] = useState<GameState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connectWebSocket = useCallback((gameId: string) => {
    if (!isAuthenticated || !user) return;

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:5000'}/game/${gameId}`;
    const token = localStorage.getItem('token');
    
    const ws = new WebSocket(`${wsUrl}?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after a delay if game is still active
      if (currentGame && currentGame.status === 'in_progress') {
        setTimeout(() => {
          connectWebSocket(gameId);
        }, 3000);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error occurred');
    };

    setWebsocket(ws);
  }, [isAuthenticated, user, currentGame]);

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'game_update':
        setCurrentGame(message.data as GameState);
        break;
      
      case 'chat_message':
        setChatMessages(prev => [...prev, message.data as ChatMessage]);
        break;
      
      case 'player_joined':
        console.log('Player joined:', message.data);
        break;
      
      case 'player_left':
        console.log('Player left:', message.data);
        break;
      
      case 'round_start':
        console.log('Round started:', message.data);
        setCurrentGame(prev => prev ? { ...prev, ...message.data } : null);
        break;
      
      case 'round_end':
        console.log('Round ended:', message.data);
        setCurrentGame(prev => prev ? { ...prev, ...message.data } : null);
        break;
      
      case 'game_end':
        console.log('Game ended:', message.data);
        setCurrentGame(prev => prev ? { ...prev, status: 'completed', ...message.data } : null);
        break;
      
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const joinGame = async (gameId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const game = await apiClient.games.get(gameId);
      setCurrentGame(game);
      setChatMessages([]); // Reset chat for new game
      
      // Connect to WebSocket for real-time updates
      connectWebSocket(gameId);
    } catch (error: any) {
      setError(error.message || 'Failed to join game');
      console.error('Error joining game:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const leaveGame = () => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    
    setCurrentGame(null);
    setChatMessages([]);
    setIsConnected(false);
    setError(null);
  };

  const makeMove = async (move: Omit<GameMove, 'gameId'>) => {
    if (!currentGame) {
      throw new Error('No active game');
    }

    setIsLoading(true);
    setError(null);

    try {
      const gameMove: GameMove = {
        ...move,
        gameId: currentGame.id,
      };

      const updatedGame = await apiClient.games.makeMove(gameMove);
      setCurrentGame(updatedGame);
    } catch (error: any) {
      setError(error.message || 'Failed to make move');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const sendChatMessage = (message: string) => {
    if (!websocket || !currentGame || !user) return;

    const chatMessage = {
      type: 'chat_message',
      data: {
        gameId: currentGame.id,
        playerId: user.id,
        playerName: user.firstName || user.username,
        message: message.trim(),
        timestamp: new Date().toISOString(),
      },
    };

    websocket.send(JSON.stringify(chatMessage));
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [websocket]);

  const value: GameContextType = {
    currentGame,
    isConnected,
    chatMessages,
    joinGame,
    leaveGame,
    makeMove,
    sendChatMessage,
    isLoading,
    error,
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
};