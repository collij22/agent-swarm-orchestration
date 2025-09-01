using CountdownGame.Server.Services;
using CountdownGame.Server.Data;
using CountdownGame.Shared.Models;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace CountdownGame.Server.Tests.Services;

[TestClass]
public class EloRatingServiceTests
{
    private GameDbContext _dbContext = null!;
    private EloRatingService _eloService = null!;

    [TestInitialize]
    public void Setup()
    {
        var options = new DbContextOptionsBuilder<GameDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;

        _dbContext = new GameDbContext(options);
        _eloService = new EloRatingService(_dbContext);
    }

    [TestCleanup]
    public void Cleanup()
    {
        _dbContext.Dispose();
    }

    [TestMethod]
    public async Task GetPlayerRatingAsync_ShouldReturnDefaultRatingForNewPlayer()
    {
        // Arrange
        var playerId = Guid.NewGuid();

        // Act
        var rating = await _eloService.GetPlayerRatingAsync(playerId);

        // Assert
        rating.Should().Be(1500, "New players should start with 1500 ELO rating as per requirements");
    }

    [TestMethod]
    public async Task UpdateRatingsAsync_ShouldUpdateBothPlayerRatings()
    {
        // Arrange
        var winnerId = Guid.NewGuid();
        var loserId = Guid.NewGuid();
        
        // Set initial ratings
        await _eloService.SetPlayerRatingAsync(winnerId, 1500);
        await _eloService.SetPlayerRatingAsync(loserId, 1500);

        // Act
        await _eloService.UpdateRatingsAsync(winnerId, loserId, false); // Not a draw

        // Assert
        var winnerRating = await _eloService.GetPlayerRatingAsync(winnerId);
        var loserRating = await _eloService.GetPlayerRatingAsync(loserId);

        winnerRating.Should().BeGreaterThan(1500, "Winner should gain rating points");
        loserRating.Should().BeLessThan(1500, "Loser should lose rating points");
        
        // Total rating should be conserved (approximately)
        var totalRatingChange = (winnerRating - 1500) + (loserRating - 1500);
        Math.Abs(totalRatingChange).Should().BeLessThan(1, "Rating system should be approximately zero-sum");
    }

    [TestMethod]
    public async Task UpdateRatingsAsync_ShouldHandleDraws()
    {
        // Arrange
        var player1Id = Guid.NewGuid();
        var player2Id = Guid.NewGuid();
        
        await _eloService.SetPlayerRatingAsync(player1Id, 1500);
        await _eloService.SetPlayerRatingAsync(player2Id, 1500);

        // Act
        await _eloService.UpdateRatingsAsync(player1Id, player2Id, true); // Draw

        // Assert
        var player1Rating = await _eloService.GetPlayerRatingAsync(player1Id);
        var player2Rating = await _eloService.GetPlayerRatingAsync(player2Id);

        // In a draw between equal-rated players, ratings should remain the same
        player1Rating.Should().Be(1500);
        player2Rating.Should().Be(1500);
    }

    [TestMethod]
    public async Task UpdateRatingsAsync_ShouldUseHigherKFactorForNewPlayers()
    {
        // Arrange
        var newPlayerId = Guid.NewGuid();
        var experiencedPlayerId = Guid.NewGuid();
        
        await _eloService.SetPlayerRatingAsync(newPlayerId, 1500);
        await _eloService.SetPlayerRatingAsync(experiencedPlayerId, 1500);
        
        // Simulate experienced player having many games
        await _eloService.RecordGameAsync(experiencedPlayerId);
        for (int i = 0; i < 30; i++)
        {
            await _eloService.RecordGameAsync(experiencedPlayerId);
        }

        var initialNewPlayerRating = await _eloService.GetPlayerRatingAsync(newPlayerId);
        var initialExperiencedRating = await _eloService.GetPlayerRatingAsync(experiencedPlayerId);

        // Act - new player wins
        await _eloService.UpdateRatingsAsync(newPlayerId, experiencedPlayerId, false);

        // Assert
        var newPlayerRatingChange = await _eloService.GetPlayerRatingAsync(newPlayerId) - initialNewPlayerRating;
        var experiencedPlayerRatingChange = Math.Abs(await _eloService.GetPlayerRatingAsync(experiencedPlayerId) - initialExperiencedRating);

        newPlayerRatingChange.Should().BeGreaterThan(experiencedPlayerRatingChange,
            "New players should have larger rating changes due to higher K-factor");
    }

    [TestMethod]
    public async Task UpdateRatingsAsync_ShouldGiveMorePointsForUpsets()
    {
        // Arrange
        var lowRatedPlayerId = Guid.NewGuid();
        var highRatedPlayerId = Guid.NewGuid();
        
        await _eloService.SetPlayerRatingAsync(lowRatedPlayerId, 1200);
        await _eloService.SetPlayerRatingAsync(highRatedPlayerId, 1800);

        // Act - underdog wins
        await _eloService.UpdateRatingsAsync(lowRatedPlayerId, highRatedPlayerId, false);

        // Assert
        var lowRatedPlayerGain = await _eloService.GetPlayerRatingAsync(lowRatedPlayerId) - 1200;
        var highRatedPlayerLoss = 1800 - await _eloService.GetPlayerRatingAsync(highRatedPlayerId);

        lowRatedPlayerGain.Should().BeGreaterThan(20, "Underdog should gain significant points for upset victory");
        highRatedPlayerLoss.Should().BeGreaterThan(20, "Favorite should lose significant points for upset loss");
    }

    [TestMethod]
    public async Task GetLeaderboardAsync_ShouldReturnTopPlayersByRating()
    {
        // Arrange
        var players = new List<Guid>();
        for (int i = 0; i < 10; i++)
        {
            var playerId = Guid.NewGuid();
            players.Add(playerId);
            await _eloService.SetPlayerRatingAsync(playerId, 1500 + (i * 100));
        }

        // Act
        var leaderboard = await _eloService.GetLeaderboardAsync(5);

        // Assert
        leaderboard.Should().HaveCount(5);
        
        // Should be ordered by rating descending
        for (int i = 0; i < leaderboard.Count - 1; i++)
        {
            leaderboard[i].Rating.Should().BeGreaterOrEqualTo(leaderboard[i + 1].Rating);
        }
        
        leaderboard[0].Rating.Should().Be(2400); // Highest rating
    }

    [TestMethod]
    public async Task GetPlayerStatsAsync_ShouldReturnAccurateStatistics()
    {
        // Arrange
        var playerId = Guid.NewGuid();
        await _eloService.SetPlayerRatingAsync(playerId, 1600);
        
        // Record some games
        for (int i = 0; i < 5; i++)
        {
            await _eloService.RecordGameAsync(playerId);
        }

        // Act
        var stats = await _eloService.GetPlayerStatsAsync(playerId);

        // Assert
        stats.Should().NotBeNull();
        stats.CurrentRating.Should().Be(1600);
        stats.GamesPlayed.Should().Be(5);
        stats.PlayerId.Should().Be(playerId);
    }

    [TestMethod]
    public async Task CalculateExpectedScore_ShouldReturnValidProbabilities()
    {
        // Arrange
        var rating1 = 1600;
        var rating2 = 1400;

        // Act
        var expectedScore1 = _eloService.CalculateExpectedScore(rating1, rating2);
        var expectedScore2 = _eloService.CalculateExpectedScore(rating2, rating1);

        // Assert
        expectedScore1.Should().BeInRange(0.0, 1.0, "Expected score should be a probability");
        expectedScore2.Should().BeInRange(0.0, 1.0, "Expected score should be a probability");
        
        expectedScore1.Should().BeGreaterThan(0.5, "Higher rated player should be favored");
        expectedScore2.Should().BeLessThan(0.5, "Lower rated player should be underdog");
        
        Math.Abs((expectedScore1 + expectedScore2) - 1.0).Should().BeLessThan(0.001,
            "Expected scores should sum to 1.0");
    }

    [TestMethod]
    public async Task GetKFactor_ShouldVaryBasedOnGamesPlayedAndRating()
    {
        // Arrange
        var newPlayerId = Guid.NewGuid();
        var experiencedPlayerId = Guid.NewGuid();
        var masterPlayerId = Guid.NewGuid();

        await _eloService.SetPlayerRatingAsync(newPlayerId, 1500);
        await _eloService.SetPlayerRatingAsync(experiencedPlayerId, 1500);
        await _eloService.SetPlayerRatingAsync(masterPlayerId, 2200);

        // Simulate games played
        for (int i = 0; i < 30; i++)
        {
            await _eloService.RecordGameAsync(experiencedPlayerId);
        }

        // Act
        var newPlayerK = await _eloService.GetKFactorAsync(newPlayerId);
        var experiencedPlayerK = await _eloService.GetKFactorAsync(experiencedPlayerId);
        var masterPlayerK = await _eloService.GetKFactorAsync(masterPlayerId);

        // Assert
        newPlayerK.Should().BeGreaterThan(experiencedPlayerK, 
            "New players should have higher K-factor for faster rating adjustment");
        masterPlayerK.Should().BeLessThan(experiencedPlayerK,
            "Master-level players should have lower K-factor for rating stability");
    }

    [TestMethod]
    public async Task RatingHistory_ShouldTrackRatingChanges()
    {
        // Arrange
        var playerId = Guid.NewGuid();
        await _eloService.SetPlayerRatingAsync(playerId, 1500);

        // Act - simulate rating changes
        await _eloService.SetPlayerRatingAsync(playerId, 1520);
        await _eloService.SetPlayerRatingAsync(playerId, 1480);
        await _eloService.SetPlayerRatingAsync(playerId, 1550);

        var history = await _eloService.GetRatingHistoryAsync(playerId);

        // Assert
        history.Should().NotBeEmpty();
        history.Should().BeInDescendingOrder(h => h.Date, "History should be ordered by date descending");
        
        var latestRating = history.First().Rating;
        latestRating.Should().Be(1550, "Latest history entry should match current rating");
    }

    [TestMethod]
    public async Task Performance_RatingCalculations_ShouldBeEfficient()
    {
        // Arrange
        var players = new List<Guid>();
        for (int i = 0; i < 100; i++)
        {
            var playerId = Guid.NewGuid();
            players.Add(playerId);
            await _eloService.SetPlayerRatingAsync(playerId, 1500 + (i * 10));
        }

        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        // Act - perform many rating updates
        for (int i = 0; i < 50; i++)
        {
            var player1 = players[i];
            var player2 = players[i + 1];
            await _eloService.UpdateRatingsAsync(player1, player2, false);
        }

        // Assert
        stopwatch.Stop();
        stopwatch.ElapsedMilliseconds.Should().BeLessThan(2000,
            "50 rating updates should complete within 2 seconds");
    }

    [TestMethod]
    public async Task RatingFloor_ShouldPreventNegativeRatings()
    {
        // Arrange
        var weakPlayerId = Guid.NewGuid();
        var strongPlayerId = Guid.NewGuid();
        
        await _eloService.SetPlayerRatingAsync(weakPlayerId, 100); // Very low rating
        await _eloService.SetPlayerRatingAsync(strongPlayerId, 2000);

        // Act - weak player loses many games
        for (int i = 0; i < 10; i++)
        {
            await _eloService.UpdateRatingsAsync(strongPlayerId, weakPlayerId, false);
        }

        // Assert
        var weakPlayerRating = await _eloService.GetPlayerRatingAsync(weakPlayerId);
        weakPlayerRating.Should().BeGreaterThan(0, "Rating should never go below 0");
        weakPlayerRating.Should().BeGreaterOrEqualTo(100, "Rating should have a reasonable floor");
    }

    [TestMethod]
    public void ValidateEloFormula_ShouldMatchStandardImplementation()
    {
        // Test the mathematical correctness of ELO calculations
        // Using known values from ELO rating literature

        // Arrange
        var rating1 = 1613;
        var rating2 = 1573;

        // Act
        var expected1 = _eloService.CalculateExpectedScore(rating1, rating2);
        var expected2 = _eloService.CalculateExpectedScore(rating2, rating1);

        // Assert
        // These values are from standard ELO calculation examples
        expected1.Should().BeApproximately(0.557, 0.01, "Expected score should match standard ELO calculation");
        expected2.Should().BeApproximately(0.443, 0.01, "Expected score should match standard ELO calculation");
    }
}