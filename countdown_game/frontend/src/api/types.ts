// Game State Types
export interface GameState {
  id: string;
  status: 'waiting' | 'in_progress' | 'completed';
  currentRound: number;
  totalRounds: number;
  currentPlayer: number;
  timeRemaining: number;
  roundType: 'letters' | 'numbers' | 'conundrum';
  player1Score: number;
  player2Score: number;
  createdAt: string;
  updatedAt: string;
}

export interface Player {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  eloRating: number;
  gamesPlayed: number;
  gamesWon: number;
  createdAt: string;
  isOnline?: boolean;
}

export interface LettersRound {
  id: string;
  gameId: string;
  roundNumber: number;
  selectedLetters: string[];
  vowelCount: number;
  consonantCount: number;
  player1Word?: string;
  player2Word?: string;
  player1Score: number;
  player2Score: number;
  timeRemaining: number;
  status: 'selecting' | 'playing' | 'completed';
}

export interface NumbersRound {
  id: string;
  gameId: string;
  roundNumber: number;
  selectedNumbers: number[];
  targetNumber: number;
  player1Expression?: string;
  player2Expression?: string;
  player1Score: number;
  player2Score: number;
  timeRemaining: number;
  status: 'selecting' | 'playing' | 'completed';
}

export interface ConundrumRound {
  id: string;
  gameId: string;
  roundNumber: number;
  scrambledWord: string;
  solution: string;
  winner?: number;
  timeRemaining: number;
  status: 'playing' | 'completed';
  buzzedPlayer?: number;
}

// API Request/Response Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  password: string;
}

export interface AuthResponse {
  user: Player;
  accessToken: string;
  refreshToken: string;
}

export interface CreateGameRequest {
  gameMode: 'single_player' | 'multiplayer' | 'practice';
  difficulty?: 'easy' | 'medium' | 'hard';
  isRated?: boolean;
}

export interface JoinGameRequest {
  gameId: string;
  inviteCode?: string;
}

export interface GameMove {
  gameId: string;
  roundNumber: number;
  moveType: 'select_letter' | 'select_number' | 'submit_word' | 'submit_expression' | 'buzz_conundrum';
  data: any;
}

export interface LeaderboardEntry {
  rank: number;
  player: Player;
  rating: number;
  gamesPlayed: number;
  winRate: number;
}

export interface GameHistory {
  id: string;
  opponent: Player | null;
  gameMode: string;
  finalScore: string;
  result: 'win' | 'loss' | 'draw';
  rating: number;
  ratingChange: number;
  duration: number;
  playedAt: string;
}

export interface GameStatistics {
  totalGames: number;
  gamesWon: number;
  gamesLost: number;
  winRate: number;
  currentRating: number;
  highestRating: number;
  averageScore: number;
  bestWord?: string;
  bestWordScore: number;
  perfectNumbers: number;
  conundrumsWon: number;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'game_update' | 'player_joined' | 'player_left' | 'round_start' | 'round_end' | 'game_end' | 'chat_message';
  data: any;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  gameId: string;
  playerId: string;
  playerName: string;
  message: string;
  timestamp: string;
}

// Dictionary and Validation Types
export interface WordValidation {
  word: string;
  isValid: boolean;
  definition?: string;
  score: number;
}

export interface NumbersValidation {
  expression: string;
  isValid: boolean;
  result: number;
  score: number;
}

// Error Types
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

// Pagination Types
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface QueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}