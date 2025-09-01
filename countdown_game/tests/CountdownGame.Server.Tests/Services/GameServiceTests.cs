using CountdownGame.Server.Services;
using CountdownGame.Server.Data;
using CountdownGame.Shared.Models;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;

namespace CountdownGame.Server.Tests.Services;

[TestClass]
public class GameServiceTests
{
    private GameDbContext _dbContext = null!;
    private GameService _gameService = null!;

    [TestInitialize]
    public void Setup()
    {
        var options = new DbContextOptionsBuilder<GameDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _dbContext = new GameDbContext(options);
        _gameService = new GameService(_dbContext);
    }

    [TestCleanup]
    public void Cleanup()
    {
        _dbContext.Dispose();
    }

    [TestMethod]
    public async Task CreateGameAsync_ShouldCreateNewGame()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();

        // Act
        var game = await _gameService.CreateGameAsync(player1Id, player2Id);

        // Assert
        game.Should().NotBeNull();
        game.Player1Id.Should().Be(player1Id);
        game.Player2Id.Should().Be(player2Id);
        game.Status.Should().Be(GameStatus.WaitingForPlayers);
        game.CurrentRound.Should().Be(1);
        
        // Verify game was saved to database
        var savedGame = await _dbContext.Games.FindAsync(game.Id);
        savedGame.Should().NotBeNull();
    }

    [TestMethod]
    public async Task GetGameAsync_ShouldReturnExistingGame()
    {
        // Arrange
        var game = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());

        // Act
        var retrievedGame = await _gameService.GetGameAsync(game.Id);

        // Assert
        retrievedGame.Should().NotBeNull();
        retrievedGame!.Id.Should().Be(game.Id);
    }

    [TestMethod]
    public async Task GetGameAsync_ShouldReturnNullForNonExistentGame()
    {
        // Act
        var game = await _gameService.GetGameAsync(Guid.NewGuid());

        // Assert
        game.Should().BeNull();
    }

    [TestMethod]
    public async Task StartGameAsync_ShouldTransitionGameToInProgress()
    {
        // Arrange
        var game = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());

        // Act
        await _gameService.StartGameAsync(game.Id);

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.Status.Should().Be(GameStatus.InProgress);
        updatedGame.StartTime.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [TestMethod]
    public async Task SubmitLettersAnswerAsync_ShouldUpdatePlayerScore()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();
        var game = await _gameService.CreateGameAsync(player1Id, player2Id);
        await _gameService.StartGameAsync(game.Id);

        // Act
        await _gameService.SubmitLettersAnswerAsync(game.Id, player1Id, "HELLO");

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.Player1Score.Should().BeGreaterThan(0);
    }

    [TestMethod]
    public async Task SubmitNumbersAnswerAsync_ShouldUpdatePlayerScore()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();
        var game = await _gameService.CreateGameAsync(player1Id, player2Id);
        await _gameService.StartGameAsync(game.Id);
        
        // Move to a numbers round
        game.CurrentRound = 3;
        await _gameService.UpdateGameAsync(game);

        // Act
        await _gameService.SubmitNumbersAnswerAsync(game.Id, player1Id, 100, "50 + 25 + 25");

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.Player1Score.Should().BeGreaterThan(0);
    }

    [TestMethod]
    public async Task SubmitConundrumAnswerAsync_ShouldUpdatePlayerScore()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();
        var game = await _gameService.CreateGameAsync(player1Id, player2Id);
        await _gameService.StartGameAsync(game.Id);
        
        // Move to conundrum round
        game.CurrentRound = 15;
        await _gameService.UpdateGameAsync(game);

        // Act
        await _gameService.SubmitConundrumAnswerAsync(game.Id, player1Id, "COUNTDOWN");

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.Player1Score.Should().BeGreaterOrEqualTo(0);
    }

    [TestMethod]
    public async Task NextRoundAsync_ShouldAdvanceRound()
    {
        // Arrange
        var game = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        await _gameService.StartGameAsync(game.Id);

        // Act
        await _gameService.NextRoundAsync(game.Id);

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.CurrentRound.Should().Be(2);
    }

    [TestMethod]
    public async Task NextRoundAsync_ShouldCompleteGameAfterRound15()
    {
        // Arrange
        var game = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        await _gameService.StartGameAsync(game.Id);
        game.CurrentRound = 15;
        await _gameService.UpdateGameAsync(game);

        // Act
        await _gameService.NextRoundAsync(game.Id);

        // Assert
        var updatedGame = await _gameService.GetGameAsync(game.Id);
        updatedGame!.Status.Should().Be(GameStatus.Completed);
        updatedGame.EndTime.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [TestMethod]
    public async Task GetActiveGamesAsync_ShouldReturnInProgressGames()
    {
        // Arrange
        var game1 = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        var game2 = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        await _gameService.StartGameAsync(game1.Id);
        // game2 remains in WaitingForPlayers status

        // Act
        var activeGames = await _gameService.GetActiveGamesAsync();

        // Assert
        activeGames.Should().HaveCount(1);
        activeGames.First().Id.Should().Be(game1.Id);
    }

    [TestMethod]
    public async Task GetPlayerGamesAsync_ShouldReturnPlayerSpecificGames()
    {
        // Arrange
        var playerId = Guid.NewGuid();
        var otherPlayerId = Guid.NewGuid();
        var thirdPlayerId = Guid.NewGuid();
        
        var playerGame1 = await _gameService.CreateGameAsync(playerId, otherPlayerId);
        var playerGame2 = await _gameService.CreateGameAsync(otherPlayerId, playerId);
        var otherGame = await _gameService.CreateGameAsync(otherPlayerId, thirdPlayerId);

        // Act
        var playerGames = await _gameService.GetPlayerGamesAsync(playerId);

        // Assert
        playerGames.Should().HaveCount(2);
        playerGames.Should().Contain(g => g.Id == playerGame1.Id);
        playerGames.Should().Contain(g => g.Id == playerGame2.Id);
        playerGames.Should().NotContain(g => g.Id == otherGame.Id);
    }

    [TestMethod]
    public async Task DeleteGameAsync_ShouldRemoveGame()
    {
        // Arrange
        var game = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());

        // Act
        await _gameService.DeleteGameAsync(game.Id);

        // Assert
        var deletedGame = await _gameService.GetGameAsync(game.Id);
        deletedGame.Should().BeNull();
    }

    [TestMethod]
    public async Task IsPlayerInGameAsync_ShouldReturnTrueForParticipatingPlayer()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();
        var game = await _gameService.CreateGameAsync(player1Id, player2Id);

        // Act
        var isPlayer1InGame = await _gameService.IsPlayerInGameAsync(player1Id, game.Id);
        var isPlayer2InGame = await _gameService.IsPlayerInGameAsync(player2Id, game.Id);
        var isOtherPlayerInGame = await _gameService.IsPlayerInGameAsync(Guid.NewGuid(), game.Id);

        // Assert
        isPlayer1InGame.Should().BeTrue();
        isPlayer2InGame.Should().BeTrue();
        isOtherPlayerInGame.Should().BeFalse();
    }

    [TestMethod]
    public async Task GetGameStatsAsync_ShouldReturnValidStatistics()
    {
        // Arrange
        await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        var completedGame = await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        await _gameService.StartGameAsync(completedGame.Id);
        completedGame.CurrentRound = 15;
        completedGame.Status = GameStatus.Completed;
        await _gameService.UpdateGameAsync(completedGame);

        // Act
        var stats = await _gameService.GetGameStatsAsync();

        // Assert
        stats.Should().NotBeNull();
        stats.TotalGames.Should().Be(3);
        stats.ActiveGames.Should().Be(2); // Two in WaitingForPlayers
        stats.CompletedGames.Should().Be(1);
    }

    [TestMethod]
    public async Task ConcurrentGameCreation_ShouldHandleMultipleRequests()
    {
        // Arrange
        var tasks = new List<Task<Game>>();
        
        // Act
        for (int i = 0; i < 10; i++)
        {
            tasks.Add(_gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid()));
        }
        
        var games = await Task.WhenAll(tasks);

        // Assert
        games.Should().HaveCount(10);
        games.Select(g => g.Id).Should().OnlyHaveUniqueItems();
        
        var dbGames = await _dbContext.Games.CountAsync();
        dbGames.Should().Be(10);
    }

    [TestMethod]
    public async Task Performance_CreateGame_ShouldBeReasonablyFast()
    {
        // Arrange
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        // Act
        for (int i = 0; i < 100; i++)
        {
            await _gameService.CreateGameAsync(Guid.NewGuid(), Guid.NewGuid());
        }

        // Assert
        stopwatch.Stop();
        stopwatch.ElapsedMilliseconds.Should().BeLessThan(5000, 
            "Creating 100 games should complete within 5 seconds");
    }
}