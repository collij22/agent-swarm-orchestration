using CountdownGame.Shared.Models;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;

namespace CountdownGame.Server.Data;

public class GameDbContext : DbContext
{
    public GameDbContext(DbContextOptions<GameDbContext> options) : base(options) { }

    public DbSet<PlayerEntity> Players { get; set; }
    public DbSet<GameSessionEntity> Games { get; set; }
    public DbSet<GameStatisticsEntity> Statistics { get; set; }
    public DbSet<MatchHistoryEntity> MatchHistory { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Player entity configuration
        modelBuilder.Entity<PlayerEntity>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(50);
            entity.Property(e => e.EloRating).HasDefaultValue(1500);
            entity.HasIndex(e => e.Name).IsUnique();
            entity.HasIndex(e => e.EloRating);
        });

        // Game session entity configuration
        modelBuilder.Entity<GameSessionEntity>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Mode).HasConversion<string>();
            entity.Property(e => e.State).HasConversion<string>();
            entity.Property(e => e.PlayersJson).HasColumnType("TEXT");
            entity.Property(e => e.RoundsJson).HasColumnType("TEXT");
            entity.HasIndex(e => e.InviteCode).IsUnique();
            entity.HasIndex(e => e.CreatedAt);
            entity.HasIndex(e => e.State);
        });

        // Statistics entity configuration
        modelBuilder.Entity<GameStatisticsEntity>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.PlayerId).IsRequired();
            entity.HasIndex(e => e.PlayerId).IsUnique();
            
            entity.HasOne<PlayerEntity>()
                .WithMany()
                .HasForeignKey(e => e.PlayerId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Match history entity configuration
        modelBuilder.Entity<MatchHistoryEntity>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.GameMode).HasConversion<string>();
            entity.HasIndex(e => e.PlayerId);
            entity.HasIndex(e => e.PlayedAt);
            
            entity.HasOne<PlayerEntity>()
                .WithMany()
                .HasForeignKey(e => e.PlayerId)
                .OnDelete(DeleteBehavior.Cascade);
        });
    }
}

// Entity models for database storage
public class PlayerEntity
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int EloRating { get; set; } = 1500;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime LastActive { get; set; } = DateTime.UtcNow;
    public bool IsOnline { get; set; }
}

public class GameSessionEntity
{
    public string Id { get; set; } = string.Empty;
    public GameMode Mode { get; set; }
    public GameState State { get; set; }
    public string PlayersJson { get; set; } = "[]";
    public string RoundsJson { get; set; } = "[]";
    public int CurrentRoundIndex { get; set; }
    public string? CurrentPlayerId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public string? InviteCode { get; set; }
    public string? WinnerId { get; set; }

    // Helper methods to serialize/deserialize complex objects
    public List<Player> GetPlayers()
    {
        return string.IsNullOrEmpty(PlayersJson) 
            ? new List<Player>() 
            : JsonSerializer.Deserialize<List<Player>>(PlayersJson) ?? new List<Player>();
    }

    public void SetPlayers(List<Player> players)
    {
        PlayersJson = JsonSerializer.Serialize(players);
    }

    public List<Round> GetRounds()
    {
        return string.IsNullOrEmpty(RoundsJson) 
            ? new List<Round>() 
            : JsonSerializer.Deserialize<List<Round>>(RoundsJson) ?? new List<Round>();
    }

    public void SetRounds(List<Round> rounds)
    {
        RoundsJson = JsonSerializer.Serialize(rounds);
    }

    public GameSession ToGameSession()
    {
        var players = GetPlayers();
        return new GameSession
        {
            Id = Id,
            Mode = Mode,
            State = State,
            Players = players,
            Rounds = GetRounds(),
            CurrentRoundIndex = CurrentRoundIndex,
            CurrentPlayer = players.FirstOrDefault(p => p.Id == CurrentPlayerId),
            CreatedAt = CreatedAt,
            StartedAt = StartedAt,
            CompletedAt = CompletedAt,
            InviteCode = InviteCode
        };
    }

    public static GameSessionEntity FromGameSession(GameSession game)
    {
        var entity = new GameSessionEntity
        {
            Id = game.Id,
            Mode = game.Mode,
            State = game.State,
            CurrentRoundIndex = game.CurrentRoundIndex,
            CurrentPlayerId = game.CurrentPlayer?.Id,
            CreatedAt = game.CreatedAt,
            StartedAt = game.StartedAt,
            CompletedAt = game.CompletedAt,
            InviteCode = game.InviteCode,
            WinnerId = game.Winner?.Id
        };
        
        entity.SetPlayers(game.Players);
        entity.SetRounds(game.Rounds);
        
        return entity;
    }
}

public class GameStatisticsEntity
{
    public int Id { get; set; }
    public string PlayerId { get; set; } = string.Empty;
    public int GamesPlayed { get; set; }
    public int GamesWon { get; set; }
    public int TotalScore { get; set; }
    public int CurrentStreak { get; set; }
    public int BestStreak { get; set; }
    public DateTime LastPlayed { get; set; } = DateTime.UtcNow;

    public GameStatistics ToGameStatistics()
    {
        return new GameStatistics
        {
            PlayerId = PlayerId,
            GamesPlayed = GamesPlayed,
            GamesWon = GamesWon,
            TotalScore = TotalScore,
            CurrentStreak = CurrentStreak,
            BestStreak = BestStreak,
            LastPlayed = LastPlayed
        };
    }
}

public class MatchHistoryEntity
{
    public int Id { get; set; }
    public string PlayerId { get; set; } = string.Empty;
    public string GameId { get; set; } = string.Empty;
    public GameMode GameMode { get; set; }
    public int PlayerScore { get; set; }
    public int OpponentScore { get; set; }
    public bool Won { get; set; }
    public int EloChange { get; set; }
    public DateTime PlayedAt { get; set; } = DateTime.UtcNow;
    public TimeSpan GameDuration { get; set; }
}