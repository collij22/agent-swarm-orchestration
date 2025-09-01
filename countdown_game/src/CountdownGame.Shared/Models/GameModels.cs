using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace CountdownGame.Shared.Models;

public enum GameMode
{
    SinglePlayer,
    Multiplayer,
    Practice
}

public enum RoundType
{
    Letters,
    Numbers,
    Conundrum
}

public enum GameState
{
    WaitingForPlayers,
    InProgress,
    RoundInProgress,
    RoundComplete,
    GameComplete,
    Abandoned
}

public enum AIDifficulty
{
    Easy,
    Medium,
    Hard
}

public class Player
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int Score { get; set; }
    public int EloRating { get; set; } = 1500;
    public bool IsAI { get; set; }
    public AIDifficulty? AIDifficulty { get; set; }
    public DateTime LastActivity { get; set; } = DateTime.UtcNow;
}

public class GameSession
{
    public string Id { get; set; } = string.Empty;
    public GameMode Mode { get; set; }
    public GameState State { get; set; }
    public List<Player> Players { get; set; } = new();
    public List<Round> Rounds { get; set; } = new();
    public int CurrentRoundIndex { get; set; }
    public Player? CurrentPlayer { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public string? InviteCode { get; set; }
    
    public Round? CurrentRound => CurrentRoundIndex < Rounds.Count ? Rounds[CurrentRoundIndex] : null;
    public bool IsComplete => State == GameState.GameComplete;
    public Player? Winner => IsComplete ? Players.OrderByDescending(p => p.Score).First() : null;
}

public class Round
{
    public int Number { get; set; }
    public RoundType Type { get; set; }
    public DateTime? StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public int TimeLimit { get; set; } = 30; // seconds
    public Dictionary<string, RoundResult> PlayerResults { get; set; } = new();
    
    // Letters round specific
    public List<char>? SelectedLetters { get; set; }
    
    // Numbers round specific
    public List<int>? SelectedNumbers { get; set; }
    public int? Target { get; set; }
    
    // Conundrum specific
    public string? ConundrumWord { get; set; }
    public string? ScrambledWord { get; set; }
    
    public bool IsComplete => CompletedAt.HasValue;
    public TimeSpan? Duration => StartedAt.HasValue && CompletedAt.HasValue 
        ? CompletedAt - StartedAt 
        : null;
}

public class RoundResult
{
    public string PlayerId { get; set; } = string.Empty;
    public string? Answer { get; set; }
    public int Score { get; set; }
    public DateTime? SubmittedAt { get; set; }
    public bool IsValid { get; set; }
    public string? ValidationMessage { get; set; }
    
    // Numbers round specific
    public string? Expression { get; set; }
    public int? CalculatedResult { get; set; }
    
    // Conundrum specific
    public bool BuzzedIn { get; set; }
    public DateTime? BuzzTime { get; set; }
}

public class LettersConstraints
{
    public const int TotalLetters = 9;
    public const int MinVowels = 3;
    public const int MinConsonants = 4;
    public static readonly char[] Vowels = { 'A', 'E', 'I', 'O', 'U' };
    public static readonly char[] Consonants = { 
        'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 
        'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z' 
    };
}

public class NumbersConstraints
{
    public const int TotalNumbers = 6;
    public static readonly int[] SmallNumbers = { 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10 };
    public static readonly int[] LargeNumbers = { 25, 50, 75, 100 };
    public const int MinTarget = 100;
    public const int MaxTarget = 999;
}

public class GameStatistics
{
    public string PlayerId { get; set; } = string.Empty;
    public int GamesPlayed { get; set; }
    public int GamesWon { get; set; }
    public int TotalScore { get; set; }
    public double AverageScore => GamesPlayed > 0 ? (double)TotalScore / GamesPlayed : 0;
    public double WinRate => GamesPlayed > 0 ? (double)GamesWon / GamesPlayed : 0;
    public int CurrentStreak { get; set; }
    public int BestStreak { get; set; }
    public DateTime LastPlayed { get; set; }
}