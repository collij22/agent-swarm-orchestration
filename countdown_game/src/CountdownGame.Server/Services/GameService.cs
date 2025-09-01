using CountdownGame.Server.Data;
using CountdownGame.Shared.Engine;
using CountdownGame.Shared.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Memory;

namespace CountdownGame.Server.Services;

public class GameService
{
    private readonly GameDbContext _context;
    private readonly GameEngine _gameEngine;
    private readonly EloRatingService _eloService;
    private readonly IMemoryCache _cache;
    private readonly ILogger<GameService> _logger;

    public GameService(
        GameDbContext context,
        GameEngine gameEngine,
        EloRatingService eloService,
        IMemoryCache cache,
        ILogger<GameService> logger)
    {
        _context = context;
        _gameEngine = gameEngine;
        _eloService = eloService;
        _cache = cache;
        _logger = logger;
    }

    public async Task<GameSession> CreateGame(GameMode mode, string hostPlayerId, string hostPlayerName)
    {
        var game = _gameEngine.CreateGame(mode, hostPlayerId, hostPlayerName);
        
        // Add AI player for single player mode
        if (mode == GameMode.SinglePlayer)
        {
            _gameEngine.AddAIPlayer(game, AIDifficulty.Medium); // Default to medium difficulty
        }

        // Save to database
        var gameEntity = GameSessionEntity.FromGameSession(game);
        _context.Games.Add(gameEntity);
        await _context.SaveChangesAsync();

        // Cache the game session for quick access
        _cache.Set($"game_{game.Id}", game, TimeSpan.FromHours(2));

        _logger.LogInformation("Created game {GameId} in {Mode} mode", game.Id, mode);
        return game;
    }

    public async Task<GameSession?> GetGame(string gameId)
    {
        // Try cache first
        if (_cache.TryGetValue($"game_{gameId}", out GameSession? cachedGame))
        {
            return cachedGame;
        }

        // Load from database
        var gameEntity = await _context.Games.FirstOrDefaultAsync(g => g.Id == gameId);
        if (gameEntity == null)
            return null;

        var game = gameEntity.ToGameSession();
        
        // Cache for future requests
        _cache.Set($"game_{gameId}", game, TimeSpan.FromHours(2));
        
        return game;
    }

    public async Task<GameSession?> JoinGame(string gameId, string playerId, string playerName)
    {
        var game = await GetGame(gameId);
        if (game == null)
            return null;

        var success = _gameEngine.JoinGame(game, playerId, playerName);
        if (!success)
            return null;

        await UpdateGame(game);
        return game;
    }

    public async Task<GameSession?> JoinGameByInviteCode(string inviteCode, string playerId, string playerName)
    {
        var gameEntity = await _context.Games
            .FirstOrDefaultAsync(g => g.InviteCode == inviteCode && g.State == GameState.WaitingForPlayers);
        
        if (gameEntity == null)
            return null;

        return await JoinGame(gameEntity.Id, playerId, playerName);
    }

    public async Task<GameSession?> StartGame(string gameId, string hostPlayerId)
    {
        var game = await GetGame(gameId);
        if (game == null)
            return null;

        // Verify the host is starting the game
        if (game.Players.FirstOrDefault()?.Id != hostPlayerId)
            throw new UnauthorizedAccessException("Only the host can start the game");

        _gameEngine.StartGame(game);
        await UpdateGame(game);

        return game;
    }

    public async Task<RoundResult> SubmitAnswer(string gameId, string playerId, string answer, string? expression = null)
    {
        var game = await GetGame(gameId);
        if (game == null)
            throw new ArgumentException("Game not found");

        var result = await _gameEngine.SubmitAnswer(game, playerId, answer, expression);
        await UpdateGame(game);

        // If game is complete, update ELO ratings
        if (game.IsComplete)
        {
            await UpdateEloRatings(game);
            await RecordMatchHistory(game);
        }

        return result;
    }

    public async Task<bool> BuzzIn(string gameId, string playerId)
    {
        var game = await GetGame(gameId);
        if (game == null || game.CurrentRound?.Type != RoundType.Conundrum)
            return false;

        var round = game.CurrentRound;
        if (round.PlayerResults.ContainsKey(playerId))
            return false; // Already buzzed in

        var result = new RoundResult
        {
            PlayerId = playerId,
            BuzzedIn = true,
            BuzzTime = DateTime.UtcNow
        };

        round.PlayerResults[playerId] = result;
        await UpdateGame(game);

        return true;
    }

    public async Task<GameSession?> StartNextRound(string gameId)
    {
        var game = await GetGame(gameId);
        if (game == null || game.State != GameState.RoundComplete)
            return null;

        if (game.CurrentRoundIndex < game.Rounds.Count - 1)
        {
            game.CurrentRoundIndex++;
            _gameEngine.StartRound(game);
            await UpdateGame(game);
        }

        return game;
    }

    public async Task HandleRoundTimeout(string gameId)
    {
        var game = await GetGame(gameId);
        if (game == null || game.CurrentRound == null)
            return;

        var round = game.CurrentRound;
        if (!round.IsComplete)
        {
            round.CompletedAt = DateTime.UtcNow;
            game.State = GameState.RoundComplete;

            // Update scores for submitted answers
            foreach (var result in round.PlayerResults.Values)
            {
                var player = game.Players.FirstOrDefault(p => p.Id == result.PlayerId);
                if (player != null)
                {
                    player.Score += result.Score;
                }
            }

            // Check if game is complete
            if (game.CurrentRoundIndex >= game.Rounds.Count - 1)
            {
                game.State = GameState.GameComplete;
                game.CompletedAt = DateTime.UtcNow;
                
                await UpdateEloRatings(game);
                await RecordMatchHistory(game);
            }

            await UpdateGame(game);
        }
    }

    public async Task<List<GameSession>> GetActiveGames()
    {
        var activeGameEntities = await _context.Games
            .Where(g => g.State == GameState.WaitingForPlayers || g.State == GameState.InProgress)
            .OrderByDescending(g => g.CreatedAt)
            .Take(50)
            .ToListAsync();

        return activeGameEntities.Select(e => e.ToGameSession()).ToList();
    }

    public async Task<List<GameSession>> GetPlayerGameHistory(string playerId, int limit = 20)
    {
        var gameEntities = await _context.Games
            .Where(g => g.PlayersJson.Contains(playerId) && g.State == GameState.GameComplete)
            .OrderByDescending(g => g.CompletedAt)
            .Take(limit)
            .ToListAsync();

        return gameEntities.Select(e => e.ToGameSession()).ToList();
    }

    private async Task UpdateGame(GameSession game)
    {
        var gameEntity = await _context.Games.FirstOrDefaultAsync(g => g.Id == game.Id);
        if (gameEntity != null)
        {
            // Update entity from game session
            gameEntity.State = game.State;
            gameEntity.CurrentRoundIndex = game.CurrentRoundIndex;
            gameEntity.CurrentPlayerId = game.CurrentPlayer?.Id;
            gameEntity.StartedAt = game.StartedAt;
            gameEntity.CompletedAt = game.CompletedAt;
            gameEntity.WinnerId = game.Winner?.Id;
            gameEntity.SetPlayers(game.Players);
            gameEntity.SetRounds(game.Rounds);

            await _context.SaveChangesAsync();
        }

        // Update cache
        _cache.Set($"game_{game.Id}", game, TimeSpan.FromHours(2));
    }

    private async Task UpdateEloRatings(GameSession game)
    {
        if (game.Mode != GameMode.Multiplayer || game.Players.Count != 2)
            return;

        var player1 = game.Players[0];
        var player2 = game.Players[1];

        // Skip if either player is AI
        if (player1.IsAI || player2.IsAI)
            return;

        var winner = game.Winner;
        var (newRating1, newRating2) = _eloService.CalculateNewRatings(
            player1.EloRating, player2.EloRating, 
            winner?.Id == player1.Id ? 1 : (winner?.Id == player2.Id ? 0 : 0.5));

        // Update player ratings in database
        var playerEntity1 = await _context.Players.FirstOrDefaultAsync(p => p.Id == player1.Id);
        var playerEntity2 = await _context.Players.FirstOrDefaultAsync(p => p.Id == player2.Id);

        if (playerEntity1 != null)
        {
            playerEntity1.EloRating = newRating1;
            player1.EloRating = newRating1;
        }

        if (playerEntity2 != null)
        {
            playerEntity2.EloRating = newRating2;
            player2.EloRating = newRating2;
        }

        await _context.SaveChangesAsync();

        _logger.LogInformation("Updated ELO ratings for game {GameId}: {Player1} {Rating1} -> {NewRating1}, {Player2} {Rating2} -> {NewRating2}",
            game.Id, player1.Name, player1.EloRating, newRating1, player2.Name, player2.EloRating, newRating2);
    }

    private async Task RecordMatchHistory(GameSession game)
    {
        foreach (var player in game.Players.Where(p => !p.IsAI))
        {
            var opponent = game.Players.FirstOrDefault(p => p.Id != player.Id);
            var won = game.Winner?.Id == player.Id;
            
            var eloChange = 0; // Calculate actual ELO change if needed
            
            var matchHistory = new MatchHistoryEntity
            {
                PlayerId = player.Id,
                GameId = game.Id,
                GameMode = game.Mode,
                PlayerScore = player.Score,
                OpponentScore = opponent?.Score ?? 0,
                Won = won,
                EloChange = eloChange,
                PlayedAt = game.CompletedAt ?? DateTime.UtcNow,
                GameDuration = game.CompletedAt.HasValue && game.StartedAt.HasValue 
                    ? game.CompletedAt.Value - game.StartedAt.Value 
                    : TimeSpan.Zero
            };

            _context.MatchHistory.Add(matchHistory);

            // Update player statistics
            var stats = await _context.Statistics.FirstOrDefaultAsync(s => s.PlayerId == player.Id);
            if (stats == null)
            {
                stats = new GameStatisticsEntity { PlayerId = player.Id };
                _context.Statistics.Add(stats);
            }

            stats.GamesPlayed++;
            stats.TotalScore += player.Score;
            stats.LastPlayed = DateTime.UtcNow;

            if (won)
            {
                stats.GamesWon++;
                stats.CurrentStreak++;
                if (stats.CurrentStreak > stats.BestStreak)
                    stats.BestStreak = stats.CurrentStreak;
            }
            else
            {
                stats.CurrentStreak = 0;
            }
        }

        await _context.SaveChangesAsync();
    }
}