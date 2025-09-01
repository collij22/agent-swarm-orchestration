using CountdownGame.Server.Data;
using CountdownGame.Shared.Models;
using Microsoft.EntityFrameworkCore;

namespace CountdownGame.Server.Services;

public class PlayerService
{
    private readonly GameDbContext _context;
    private readonly ILogger<PlayerService> _logger;

    public PlayerService(GameDbContext context, ILogger<PlayerService> logger)
    {
        _context = context;
        _logger = logger;
    }

    public async Task<Player?> GetPlayer(string playerId)
    {
        var playerEntity = await _context.Players.FirstOrDefaultAsync(p => p.Id == playerId);
        if (playerEntity == null)
            return null;

        return new Player
        {
            Id = playerEntity.Id,
            Name = playerEntity.Name,
            EloRating = playerEntity.EloRating
        };
    }

    public async Task<Player> CreateOrUpdatePlayer(string playerId, string playerName)
    {
        var playerEntity = await _context.Players.FirstOrDefaultAsync(p => p.Id == playerId);
        
        if (playerEntity == null)
        {
            playerEntity = new PlayerEntity
            {
                Id = playerId,
                Name = playerName,
                EloRating = 1500,
                CreatedAt = DateTime.UtcNow
            };
            _context.Players.Add(playerEntity);
        }
        else
        {
            playerEntity.Name = playerName;
            playerEntity.LastActive = DateTime.UtcNow;
        }

        playerEntity.IsOnline = true;
        await _context.SaveChangesAsync();

        _logger.LogInformation("Created/updated player {PlayerId} - {PlayerName}", playerId, playerName);

        return new Player
        {
            Id = playerEntity.Id,
            Name = playerEntity.Name,
            EloRating = playerEntity.EloRating
        };
    }

    public async Task<Player?> GetPlayerByName(string playerName)
    {
        var playerEntity = await _context.Players.FirstOrDefaultAsync(p => p.Name == playerName);
        if (playerEntity == null)
            return null;

        return new Player
        {
            Id = playerEntity.Id,
            Name = playerEntity.Name,
            EloRating = playerEntity.EloRating
        };
    }

    public async Task<List<Player>> GetLeaderboard(int limit = 100)
    {
        var playerEntities = await _context.Players
            .OrderByDescending(p => p.EloRating)
            .Take(limit)
            .ToListAsync();

        return playerEntities.Select(p => new Player
        {
            Id = p.Id,
            Name = p.Name,
            EloRating = p.EloRating
        }).ToList();
    }

    public async Task<GameStatistics?> GetPlayerStatistics(string playerId)
    {
        var stats = await _context.Statistics.FirstOrDefaultAsync(s => s.PlayerId == playerId);
        return stats?.ToGameStatistics();
    }

    public async Task<List<MatchHistoryEntity>> GetMatchHistory(string playerId, int limit = 50)
    {
        return await _context.MatchHistory
            .Where(m => m.PlayerId == playerId)
            .OrderByDescending(m => m.PlayedAt)
            .Take(limit)
            .ToListAsync();
    }

    public async Task HandlePlayerDisconnect(string playerId)
    {
        var playerEntity = await _context.Players.FirstOrDefaultAsync(p => p.Id == playerId);
        if (playerEntity != null)
        {
            playerEntity.IsOnline = false;
            playerEntity.LastActive = DateTime.UtcNow;
            await _context.SaveChangesAsync();
        }

        _logger.LogInformation("Player {PlayerId} disconnected", playerId);
    }

    public async Task<bool> IsPlayerNameAvailable(string playerName)
    {
        return !await _context.Players.AnyAsync(p => p.Name == playerName);
    }

    public async Task UpdatePlayerEloRating(string playerId, int newRating)
    {
        var playerEntity = await _context.Players.FirstOrDefaultAsync(p => p.Id == playerId);
        if (playerEntity != null)
        {
            var oldRating = playerEntity.EloRating;
            playerEntity.EloRating = newRating;
            await _context.SaveChangesAsync();

            _logger.LogInformation("Updated ELO rating for player {PlayerId}: {OldRating} -> {NewRating}", 
                playerId, oldRating, newRating);
        }
    }

    public async Task<List<Player>> GetOnlinePlayers()
    {
        var playerEntities = await _context.Players
            .Where(p => p.IsOnline)
            .OrderByDescending(p => p.LastActive)
            .ToListAsync();

        return playerEntities.Select(p => new Player
        {
            Id = p.Id,
            Name = p.Name,
            EloRating = p.EloRating
        }).ToList();
    }
}