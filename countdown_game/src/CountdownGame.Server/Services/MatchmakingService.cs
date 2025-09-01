using CountdownGame.Server.Data;
using CountdownGame.Shared.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;
using System.Collections.Concurrent;

namespace CountdownGame.Server.Services;

public class MatchmakingService
{
    private readonly GameDbContext _dbContext;
    private readonly IMemoryCache _cache;
    private readonly ILogger<MatchmakingService> _logger;
    private readonly ConcurrentDictionary<string, MatchmakingRequest> _activeRequests;
    private readonly ConcurrentDictionary<string, string> _inviteCodes;

    public MatchmakingService(
        GameDbContext dbContext,
        IMemoryCache cache,
        ILogger<MatchmakingService> logger)
    {
        _dbContext = dbContext;
        _cache = cache;
        _logger = logger;
        _activeRequests = new ConcurrentDictionary<string, MatchmakingRequest>();
        _inviteCodes = new ConcurrentDictionary<string, string>();
    }

    public async Task<MatchmakingResult> FindMatchAsync(Guid playerId, int playerElo, GameMode mode)
    {
        var request = new MatchmakingRequest
        {
            PlayerId = playerId,
            PlayerElo = playerElo,
            Mode = mode,
            CreatedAt = DateTime.UtcNow
        };

        var requestId = Guid.NewGuid().ToString();
        _activeRequests[requestId] = request;

        try
        {
            // Look for suitable opponents in the queue
            var opponent = await FindOpponentAsync(playerElo, mode);
            
            if (opponent != null)
            {
                _logger.LogInformation("Match found for player {PlayerId} with opponent {OpponentId}", 
                    playerId, opponent.PlayerId);
                
                return new MatchmakingResult
                {
                    Success = true,
                    GameId = Guid.NewGuid(),
                    OpponentId = opponent.PlayerId,
                    Message = "Match found!"
                };
            }

            // Add to waiting queue
            _logger.LogInformation("No immediate match found for player {PlayerId}, adding to queue", playerId);
            
            return new MatchmakingResult
            {
                Success = false,
                Message = "Searching for opponent...",
                QueuePosition = _activeRequests.Count
            };
        }
        finally
        {
            _activeRequests.TryRemove(requestId, out _);
        }
    }

    public string CreateInviteCode(Guid gameId)
    {
        var code = GenerateInviteCode();
        _inviteCodes[code] = gameId.ToString();
        
        // Cache for 15 minutes
        _cache.Set($"invite_{code}", gameId, TimeSpan.FromMinutes(15));
        
        _logger.LogInformation("Created invite code {Code} for game {GameId}", code, gameId);
        return code;
    }

    public async Task<JoinResult> JoinByInviteCodeAsync(string code, Guid playerId)
    {
        if (_cache.TryGetValue($"invite_{code}", out Guid gameId))
        {
            var game = await _dbContext.Games.FindAsync(gameId);
            
            if (game == null)
            {
                return new JoinResult { Success = false, Message = "Game not found" };
            }

            if (game.State != GameState.WaitingForPlayers)
            {
                return new JoinResult { Success = false, Message = "Game has already started" };
            }

            _logger.LogInformation("Player {PlayerId} joined game {GameId} via invite code", playerId, gameId);
            
            return new JoinResult
            {
                Success = true,
                GameId = gameId,
                Message = "Successfully joined game"
            };
        }

        return new JoinResult { Success = false, Message = "Invalid or expired invite code" };
    }

    public void CancelMatchmaking(Guid playerId)
    {
        var toRemove = _activeRequests
            .Where(r => r.Value.PlayerId == playerId)
            .Select(r => r.Key)
            .ToList();

        foreach (var key in toRemove)
        {
            _activeRequests.TryRemove(key, out _);
        }

        _logger.LogInformation("Cancelled matchmaking for player {PlayerId}", playerId);
    }

    public async Task<List<LobbyGame>> GetOpenGamesAsync()
    {
        var openGames = await _dbContext.Games
            .Where(g => g.State == GameState.WaitingForPlayers)
            .OrderByDescending(g => g.CreatedAt)
            .Take(20)
            .Select(g => new LobbyGame
            {
                GameId = Guid.Parse(g.Id),
                HostName = "Host", // Would be player name in real impl
                Mode = GameMode.Multiplayer,
                CreatedAt = g.CreatedAt
            })
            .ToListAsync();

        return openGames;
    }

    private async Task<MatchmakingRequest?> FindOpponentAsync(int playerElo, GameMode mode)
    {
        // Find opponents within ELO range
        var eloRange = 200; // Initial range
        var maxRange = 500;

        while (eloRange <= maxRange)
        {
            var opponent = _activeRequests.Values
                .Where(r => r.Mode == mode)
                .Where(r => Math.Abs(r.PlayerElo - playerElo) <= eloRange)
                .Where(r => DateTime.UtcNow - r.CreatedAt < TimeSpan.FromMinutes(2))
                .FirstOrDefault();

            if (opponent != null)
            {
                return opponent;
            }

            eloRange += 100;
            await Task.Delay(100); // Brief delay before expanding search
        }

        return null;
    }

    private string GenerateInviteCode()
    {
        const string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        var random = new Random();
        var code = new char[6];
        
        for (int i = 0; i < code.Length; i++)
        {
            code[i] = chars[random.Next(chars.Length)];
        }
        
        return new string(code);
    }
}

public class MatchmakingRequest
{
    public Guid PlayerId { get; set; }
    public int PlayerElo { get; set; }
    public GameMode Mode { get; set; }
    public DateTime CreatedAt { get; set; }
}

public class MatchmakingResult
{
    public bool Success { get; set; }
    public Guid? GameId { get; set; }
    public Guid? OpponentId { get; set; }
    public string Message { get; set; } = string.Empty;
    public int? QueuePosition { get; set; }
}

public class JoinResult
{
    public bool Success { get; set; }
    public Guid? GameId { get; set; }
    public string Message { get; set; } = string.Empty;
}

public class LobbyGame
{
    public Guid GameId { get; set; }
    public string HostName { get; set; } = string.Empty;
    public GameMode Mode { get; set; }
    public DateTime CreatedAt { get; set; }
}