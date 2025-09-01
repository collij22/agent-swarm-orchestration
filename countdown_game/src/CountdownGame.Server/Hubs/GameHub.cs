using CountdownGame.Server.Services;
using CountdownGame.Shared.Models;
using Microsoft.AspNetCore.SignalR;

namespace CountdownGame.Server.Hubs;

public class GameHub : Hub
{
    private readonly GameService _gameService;
    private readonly PlayerService _playerService;
    private readonly ILogger<GameHub> _logger;

    public GameHub(GameService gameService, PlayerService playerService, ILogger<GameHub> logger)
    {
        _gameService = gameService;
        _playerService = playerService;
        _logger = logger;
    }

    public override async Task OnConnectedAsync()
    {
        _logger.LogInformation("Client connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("Client disconnected: {ConnectionId}", Context.ConnectionId);
        
        // Handle player disconnect - give them 15 seconds grace period
        var playerId = Context.UserIdentifier;
        if (!string.IsNullOrEmpty(playerId))
        {
            await _playerService.HandlePlayerDisconnect(playerId);
        }
        
        await base.OnDisconnectedAsync(exception);
    }

    public async Task JoinGame(string gameId, string playerId, string playerName)
    {
        try
        {
            var game = await _gameService.JoinGame(gameId, playerId, playerName);
            if (game != null)
            {
                await Groups.AddToGroupAsync(Context.ConnectionId, gameId);
                await Clients.Group(gameId).SendAsync("PlayerJoined", new { 
                    PlayerId = playerId, 
                    PlayerName = playerName,
                    Game = game 
                });
                
                _logger.LogInformation("Player {PlayerId} joined game {GameId}", playerId, gameId);
            }
            else
            {
                await Clients.Caller.SendAsync("JoinGameFailed", "Could not join game");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error joining game {GameId} for player {PlayerId}", gameId, playerId);
            await Clients.Caller.SendAsync("JoinGameFailed", ex.Message);
        }
    }

    public async Task CreateGame(string playerId, string playerName, GameMode mode)
    {
        try
        {
            var game = await _gameService.CreateGame(mode, playerId, playerName);
            await Groups.AddToGroupAsync(Context.ConnectionId, game.Id);
            
            await Clients.Caller.SendAsync("GameCreated", game);
            _logger.LogInformation("Player {PlayerId} created game {GameId}", playerId, game.Id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating game for player {PlayerId}", playerId);
            await Clients.Caller.SendAsync("CreateGameFailed", ex.Message);
        }
    }

    public async Task StartGame(string gameId, string playerId)
    {
        try
        {
            var game = await _gameService.StartGame(gameId, playerId);
            if (game != null)
            {
                await Clients.Group(gameId).SendAsync("GameStarted", game);
                _logger.LogInformation("Game {GameId} started by player {PlayerId}", gameId, playerId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error starting game {GameId}", gameId);
            await Clients.Caller.SendAsync("StartGameFailed", ex.Message);
        }
    }

    public async Task SubmitAnswer(string gameId, string playerId, string answer, string? expression = null)
    {
        try
        {
            var result = await _gameService.SubmitAnswer(gameId, playerId, answer, expression);
            
            // Send result to all players in the game
            await Clients.Group(gameId).SendAsync("AnswerSubmitted", new {
                PlayerId = playerId,
                Result = result
            });

            // Check if round is complete
            var game = await _gameService.GetGame(gameId);
            if (game != null && game.State == GameState.RoundComplete)
            {
                await Clients.Group(gameId).SendAsync("RoundComplete", game.CurrentRound);
                
                // Auto-start next round after delay
                _ = Task.Run(async () =>
                {
                    await Task.Delay(3000); // 3 second delay
                    await StartNextRound(gameId);
                });
            }
            else if (game != null && game.State == GameState.GameComplete)
            {
                await Clients.Group(gameId).SendAsync("GameComplete", game);
            }
            
            _logger.LogInformation("Answer submitted for game {GameId} by player {PlayerId}", gameId, playerId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error submitting answer for game {GameId}", gameId);
            await Clients.Caller.SendAsync("SubmitAnswerFailed", ex.Message);
        }
    }

    public async Task BuzzIn(string gameId, string playerId)
    {
        try
        {
            var success = await _gameService.BuzzIn(gameId, playerId);
            if (success)
            {
                await Clients.Group(gameId).SendAsync("PlayerBuzzedIn", new {
                    PlayerId = playerId,
                    Timestamp = DateTime.UtcNow
                });
                
                _logger.LogInformation("Player {PlayerId} buzzed in for game {GameId}", playerId, gameId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error buzzing in for game {GameId}", gameId);
            await Clients.Caller.SendAsync("BuzzInFailed", ex.Message);
        }
    }

    public async Task SendChatMessage(string gameId, string playerId, string message)
    {
        try
        {
            var player = await _playerService.GetPlayer(playerId);
            if (player != null)
            {
                await Clients.Group(gameId).SendAsync("ChatMessage", new {
                    PlayerId = playerId,
                    PlayerName = player.Name,
                    Message = message,
                    Timestamp = DateTime.UtcNow
                });
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending chat message in game {GameId}", gameId);
        }
    }

    public async Task GetGameState(string gameId)
    {
        try
        {
            var game = await _gameService.GetGame(gameId);
            if (game != null)
            {
                await Clients.Caller.SendAsync("GameStateUpdate", game);
            }
            else
            {
                await Clients.Caller.SendAsync("GameNotFound", gameId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting game state for {GameId}", gameId);
            await Clients.Caller.SendAsync("GetGameStateFailed", ex.Message);
        }
    }

    private async Task StartNextRound(string gameId)
    {
        try
        {
            var game = await _gameService.StartNextRound(gameId);
            if (game != null)
            {
                await Clients.Group(gameId).SendAsync("RoundStarted", game.CurrentRound);
                
                // Start round timer
                _ = Task.Run(async () =>
                {
                    var round = game.CurrentRound;
                    if (round != null)
                    {
                        await Task.Delay(round.TimeLimit * 1000);
                        await HandleRoundTimeout(gameId);
                    }
                });
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error starting next round for game {GameId}", gameId);
        }
    }

    private async Task HandleRoundTimeout(string gameId)
    {
        try
        {
            await _gameService.HandleRoundTimeout(gameId);
            var game = await _gameService.GetGame(gameId);
            
            if (game != null)
            {
                await Clients.Group(gameId).SendAsync("RoundTimeout", game.CurrentRound);
                
                if (game.State == GameState.GameComplete)
                {
                    await Clients.Group(gameId).SendAsync("GameComplete", game);
                }
                else
                {
                    // Start next round after timeout
                    _ = Task.Run(async () =>
                    {
                        await Task.Delay(3000);
                        await StartNextRound(gameId);
                    });
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error handling round timeout for game {GameId}", gameId);
        }
    }
}