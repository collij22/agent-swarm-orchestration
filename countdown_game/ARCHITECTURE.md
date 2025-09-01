# Countdown Game - System Architecture

## Overview
Windows desktop application implementing Channel 4's Countdown game show with both single-player and multiplayer modes.

## Technology Stack

### Client Application (Windows Desktop)
- **Framework**: WinUI 3 (.NET 8)
- **Language**: C# 11
- **UI Pattern**: MVVM (Model-View-ViewModel)
- **Local Database**: SQLite with Entity Framework Core
- **Real-time Communication**: SignalR Client

### Backend Services (Multiplayer)
- **API Framework**: ASP.NET Core 8.0
- **Real-time**: SignalR Hubs
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Authentication**: JWT with refresh tokens
- **Hosting**: Azure App Service or self-hosted

## Project Structure

```
countdown-game/
├── src/
│   ├── Countdown.Client/              # WinUI 3 Desktop Application
│   │   ├── Views/                     # XAML Views
│   │   │   ├── MainWindow.xaml
│   │   │   ├── GameView.xaml
│   │   │   ├── LobbyView.xaml
│   │   │   └── ProfileView.xaml
│   │   ├── ViewModels/                # MVVM ViewModels
│   │   │   ├── GameViewModel.cs
│   │   │   ├── LettersRoundViewModel.cs
│   │   │   ├── NumbersRoundViewModel.cs
│   │   │   └── ConundrumViewModel.cs
│   │   ├── Models/                    # Client Models
│   │   │   ├── Player.cs
│   │   │   ├── Round.cs
│   │   │   └── GameState.cs
│   │   ├── Services/                  # Client Services
│   │   │   ├── GameEngine.cs
│   │   │   ├── DictionaryService.cs
│   │   │   ├── AIOpponentService.cs
│   │   │   └── SignalRService.cs
│   │   ├── Controls/                  # Custom Controls
│   │   │   ├── CountdownClock.xaml
│   │   │   ├── LetterTile.xaml
│   │   │   └── NumberTile.xaml
│   │   └── Assets/                    # Images, Sounds, Fonts
│   │
│   ├── Countdown.Core/                # Shared Game Logic
│   │   ├── Rules/
│   │   │   ├── LettersRoundRules.cs
│   │   │   ├── NumbersRoundRules.cs
│   │   │   └── ConundrumRules.cs
│   │   ├── Solvers/
│   │   │   ├── AnagramSolver.cs
│   │   │   ├── NumbersSolver.cs
│   │   │   └── ConundrumSolver.cs
│   │   ├── Dictionary/
│   │   │   ├── IDictionaryProvider.cs
│   │   │   └── WordValidator.cs
│   │   └── Rating/
│   │       └── EloCalculator.cs
│   │
│   ├── Countdown.Server/              # Backend API
│   │   ├── Controllers/
│   │   │   ├── AuthController.cs
│   │   │   ├── GameController.cs
│   │   │   ├── LeaderboardController.cs
│   │   │   └── ProfileController.cs
│   │   ├── Hubs/
│   │   │   └── GameHub.cs           # SignalR Hub
│   │   ├── Services/
│   │   │   ├── MatchmakingService.cs
│   │   │   ├── GameStateService.cs
│   │   │   ├── AntiCheatService.cs
│   │   │   └── RatingService.cs
│   │   └── Data/
│   │       ├── CountdownDbContext.cs
│   │       └── Repositories/
│   │
│   └── Countdown.Tests/               # Test Projects
│       ├── Countdown.Core.Tests/
│       ├── Countdown.Client.Tests/
│       └── Countdown.Server.Tests/
│
├── database/
│   ├── migrations/                    # EF Core Migrations
│   └── seed/                         # Seed Data
│
├── deployment/
│   ├── installer/                    # Windows Installer (MSIX)
│   └── docker/                       # Docker configs for backend
│
└── docs/
    ├── API.md
    ├── GAME_RULES.md
    └── DEPLOYMENT.md
```

## Core Components

### 1. Game Engine (Client-side)
Manages game flow, round progression, and rule enforcement.

```csharp
public class GameEngine
{
    private readonly IRoundManager _roundManager;
    private readonly IScoreKeeper _scoreKeeper;
    private readonly ITimeKeeper _timeKeeper;
    
    public async Task StartGame(GameMode mode)
    {
        // Initialize 15-round game
        // Manage round progression
        // Handle scoring
    }
}
```

### 2. Round Management
Each round type has specific rules and UI behavior.

```csharp
public interface IRound
{
    RoundType Type { get; }
    int Duration { get; } // 30 seconds
    Task<RoundResult> Execute();
    bool ValidateSubmission(string submission);
}
```

### 3. Dictionary Service
Validates words with pluggable dictionary providers.

```csharp
public class DictionaryService
{
    private readonly IWordIndex _wordIndex;
    
    public bool IsValidWord(string word, SpellingProfile profile)
    {
        // Check against loaded dictionary
        // Apply spelling profile (UK/US)
        // Exclude proper nouns, hyphens, etc.
    }
    
    public List<string> FindMaxWords(char[] letters)
    {
        // Find all possible words from letter set
    }
}
```

### 4. Solvers

#### Anagram Solver (Letters Round)
```csharp
public class AnagramSolver
{
    private readonly Dictionary<string, List<string>> _anagramIndex;
    
    public List<string> Solve(char[] letters)
    {
        // Use pre-computed anagram index
        // Sort by word length
        // Return valid words
    }
}
```

#### Numbers Solver
```csharp
public class NumbersSolver
{
    public Solution FindSolution(int[] numbers, int target)
    {
        // BFS/DFS with memoization
        // Maintain positive integers only
        // Track operation sequence
    }
}
```

### 5. AI Opponent System
Provides three difficulty levels with realistic behavior.

```csharp
public class AIOpponent
{
    private readonly Difficulty _difficulty;
    
    public async Task<string> PlayLettersRound(char[] letters)
    {
        // Simulate thinking time
        // Choose word based on difficulty
        // Add probabilistic errors
    }
}
```

### 6. Multiplayer Infrastructure

#### SignalR Hub (Server)
```csharp
public class GameHub : Hub
{
    public async Task JoinMatch(string matchCode)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, matchCode);
    }
    
    public async Task SubmitWord(string matchId, string word)
    {
        // Validate submission
        // Update game state
        // Broadcast to opponent
    }
}
```

#### Client Connection
```csharp
public class SignalRService
{
    private HubConnection _connection;
    
    public async Task Connect()
    {
        _connection = new HubConnectionBuilder()
            .WithUrl("https://server/gamehub")
            .WithAutomaticReconnect()
            .Build();
    }
}
```

### 7. ELO Rating System
```csharp
public class EloCalculator
{
    public (int newRatingA, int newRatingB) Calculate(
        int ratingA, int ratingB, GameResult result)
    {
        // Standard ELO formula
        // Dynamic K-factor
        // Handle provisional ratings
    }
}
```

## Data Models

### Game State
```csharp
public class GameState
{
    public Guid GameId { get; set; }
    public Player Champion { get; set; }
    public Player Challenger { get; set; }
    public List<Round> Rounds { get; set; }
    public int CurrentRound { get; set; }
    public GameStatus Status { get; set; }
}
```

### Round Data
```csharp
public class LettersRound : Round
{
    public char[] AvailableLetters { get; set; }
    public string ChampionWord { get; set; }
    public string ChallengerWord { get; set; }
    public int ChampionScore { get; set; }
    public int ChallengerScore { get; set; }
}
```

## Database Schema

### Local SQLite (Client)
```sql
CREATE TABLE Matches (
    Id TEXT PRIMARY KEY,
    Date DATETIME,
    OpponentName TEXT,
    Result TEXT,
    FinalScore TEXT,
    RoundData TEXT -- JSON
);

CREATE TABLE Settings (
    Key TEXT PRIMARY KEY,
    Value TEXT
);
```

### PostgreSQL (Server)
```sql
CREATE TABLE Users (
    Id UUID PRIMARY KEY,
    Username VARCHAR(50) UNIQUE,
    Email VARCHAR(255),
    EloRating INT DEFAULT 1500,
    GamesPlayed INT DEFAULT 0
);

CREATE TABLE Matches (
    Id UUID PRIMARY KEY,
    ChampionId UUID REFERENCES Users(Id),
    ChallengerId UUID REFERENCES Users(Id),
    StartTime TIMESTAMP,
    EndTime TIMESTAMP,
    WinnerId UUID,
    IsRated BOOLEAN,
    RoundData JSONB
);
```

## Security Considerations

### Anti-Cheat Measures
1. Server-authoritative game state
2. Time validation on server
3. Input validation and sanitization
4. Statistical analysis for superhuman play detection
5. Rate limiting on API endpoints

### Authentication Flow
1. JWT tokens with 15-minute expiry
2. Refresh tokens with 7-day expiry
3. Secure WebSocket connections for real-time

## Performance Requirements

### Client Performance
- 60 FPS animations
- <100ms input latency
- <30ms clock drift over 30 seconds

### Server Performance
- Support 500 concurrent matches
- <100ms API response time
- <50ms SignalR message delivery

## Deployment

### Client Distribution
- MSIX package for Windows Store
- MSI installer for direct download
- Auto-update mechanism

### Server Deployment
- Docker containers for backend
- Azure App Service or AWS ECS
- Redis for session caching
- PostgreSQL managed database

## Testing Strategy

### Unit Tests
- Game rules validation
- Solver algorithms
- ELO calculations
- Dictionary operations

### Integration Tests
- SignalR connectivity
- Database operations
- API endpoints

### E2E Tests
- Complete game flow
- Multiplayer synchronization
- Disconnect/reconnect scenarios

## Development Phases

### Phase 1: Core Game Engine
- Implement game rules
- Create solvers
- Build basic UI

### Phase 2: Single Player
- AI opponents
- Local storage
- Practice mode

### Phase 3: Multiplayer
- Backend API
- SignalR integration
- Matchmaking

### Phase 4: Polish
- Animations
- Sound effects
- Accessibility
- Performance optimization