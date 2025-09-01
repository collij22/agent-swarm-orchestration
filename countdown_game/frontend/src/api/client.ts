import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  Player,
  GameState,
  CreateGameRequest,
  JoinGameRequest,
  GameMove,
  LeaderboardEntry,
  GameHistory,
  GameStatistics,
  WordValidation,
  NumbersValidation,
  PaginatedResponse,
  QueryParams,
  ApiError,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Try to refresh token
          try {
            await this.auth.refresh();
            // Retry the original request
            return this.client.request(error.config!);
          } catch (refreshError) {
            // Refresh failed, logout user
            localStorage.removeItem('token');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: AxiosError): ApiError {
    if (error.response?.data) {
      return error.response.data as ApiError;
    }
    return {
      message: error.message || 'An unexpected error occurred',
      code: error.code,
    };
  }

  // Authentication endpoints
  auth = {
    login: async (credentials: LoginRequest): Promise<AuthResponse> => {
      const response = await this.client.post('/auth/login', credentials);
      const { accessToken, refreshToken, user } = response.data;
      
      localStorage.setItem('token', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
      
      return response.data;
    },

    register: async (data: RegisterRequest): Promise<AuthResponse> => {
      const response = await this.client.post('/auth/register', data);
      const { accessToken, refreshToken, user } = response.data;
      
      localStorage.setItem('token', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
      
      return response.data;
    },

    refresh: async (): Promise<AuthResponse> => {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await this.client.post('/auth/refresh', { refreshToken });
      const { accessToken, user } = response.data;
      
      localStorage.setItem('token', accessToken);
      localStorage.setItem('user', JSON.stringify(user));
      
      return response.data;
    },

    logout: async (): Promise<void> => {
      try {
        await this.client.post('/auth/logout');
      } finally {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      }
    },

    getCurrentUser: (): Player | null => {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    },
  };

  // Game management endpoints
  games = {
    create: async (data: CreateGameRequest): Promise<GameState> => {
      const response = await this.client.post('/games', data);
      return response.data;
    },

    join: async (data: JoinGameRequest): Promise<GameState> => {
      const response = await this.client.post('/games/join', data);
      return response.data;
    },

    get: async (gameId: string): Promise<GameState> => {
      const response = await this.client.get(`/games/${gameId}`);
      return response.data;
    },

    list: async (params?: QueryParams): Promise<PaginatedResponse<GameState>> => {
      const response = await this.client.get('/games', { params });
      return response.data;
    },

    makeMove: async (move: GameMove): Promise<GameState> => {
      const response = await this.client.post(`/games/${move.gameId}/moves`, move);
      return response.data;
    },

    forfeit: async (gameId: string): Promise<void> => {
      await this.client.post(`/games/${gameId}/forfeit`);
    },
  };

  // Player endpoints
  players = {
    getProfile: async (playerId?: string): Promise<Player> => {
      const endpoint = playerId ? `/players/${playerId}` : '/players/me';
      const response = await this.client.get(endpoint);
      return response.data;
    },

    updateProfile: async (data: Partial<Player>): Promise<Player> => {
      const response = await this.client.put('/players/me', data);
      return response.data;
    },

    getStatistics: async (playerId?: string): Promise<GameStatistics> => {
      const endpoint = playerId ? `/players/${playerId}/stats` : '/players/me/stats';
      const response = await this.client.get(endpoint);
      return response.data;
    },

    getGameHistory: async (params?: QueryParams): Promise<PaginatedResponse<GameHistory>> => {
      const response = await this.client.get('/players/me/history', { params });
      return response.data;
    },
  };

  // Leaderboard endpoints
  leaderboards = {
    global: async (params?: QueryParams): Promise<PaginatedResponse<LeaderboardEntry>> => {
      const response = await this.client.get('/leaderboards/global', { params });
      return response.data;
    },

    weekly: async (params?: QueryParams): Promise<PaginatedResponse<LeaderboardEntry>> => {
      const response = await this.client.get('/leaderboards/weekly', { params });
      return response.data;
    },

    friends: async (params?: QueryParams): Promise<PaginatedResponse<LeaderboardEntry>> => {
      const response = await this.client.get('/leaderboards/friends', { params });
      return response.data;
    },
  };

  // Dictionary and validation endpoints
  dictionary = {
    validateWord: async (word: string, letters: string[]): Promise<WordValidation> => {
      const response = await this.client.post('/dictionary/validate-word', { word, letters });
      return response.data;
    },

    validateNumbers: async (expression: string, numbers: number[], target: number): Promise<NumbersValidation> => {
      const response = await this.client.post('/dictionary/validate-numbers', { 
        expression, 
        numbers, 
        target 
      });
      return response.data;
    },

    getDefinition: async (word: string): Promise<{ word: string; definition: string }> => {
      const response = await this.client.get(`/dictionary/definition/${word}`);
      return response.data;
    },
  };

  // Admin endpoints (for game management)
  admin = {
    getGameStats: async (): Promise<any> => {
      const response = await this.client.get('/admin/stats');
      return response.data;
    },

    getActiveGames: async (): Promise<GameState[]> => {
      const response = await this.client.get('/admin/games/active');
      return response.data;
    },

    endGame: async (gameId: string): Promise<void> => {
      await this.client.post(`/admin/games/${gameId}/end`);
    },
  };
}

export const apiClient = new ApiClient();