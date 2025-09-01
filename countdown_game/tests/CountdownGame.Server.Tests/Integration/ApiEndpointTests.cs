using CountdownGame.Server.Data;
using CountdownGame.Shared.Models;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;

namespace CountdownGame.Server.Tests.Integration;

[TestClass]
public class ApiEndpointTests
{
    private WebApplicationFactory<Program> _factory = null!;
    private HttpClient _client = null!;
    private GameDbContext _dbContext = null!;

    [TestInitialize]
    public void Setup()
    {
        _factory = new WebApplicationFactory<Program>()
            .WithWebHostBuilder(builder =>
            {
                builder.ConfigureServices(services =>
                {
                    // Replace the database with in-memory for testing
                    var descriptor = services.SingleOrDefault(d => d.ServiceType == typeof(DbContextOptions<GameDbContext>));
                    if (descriptor != null)
                    {
                        services.Remove(descriptor);
                    }

                    services.AddDbContext<GameDbContext>(options =>
                    {
                        options.UseInMemoryDatabase($"ApiTestDb_{Guid.NewGuid()}");
                    });
                });
            });

        _client = _factory.CreateClient();
        
        // Get database context for test data setup
        using var scope = _factory.Services.CreateScope();
        _dbContext = scope.ServiceProvider.GetRequiredService<GameDbContext>();
        SeedTestData();
    }

    [TestCleanup]
    public void Cleanup()
    {
        _client.Dispose();
        _factory.Dispose();
    }

    [TestMethod]
    public async Task GET_ApiGames_ShouldReturnValidJson()
    {
        // Act
        var response = await _client.GetAsync("/api/games");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/json");
        
        var content = await response.Content.ReadAsStringAsync();
        content.Should().NotBeNullOrEmpty();
        
        // Verify it's valid JSON
        var jsonDoc = JsonDocument.Parse(content);
        jsonDoc.Should().NotBeNull();
    }

    [TestMethod]
    public async Task GET_ApiGamesById_ShouldReturnGameDetails()
    {
        // Arrange
        var game = CreateTestGame();
        await _dbContext.Games.AddAsync(game);
        await _dbContext.SaveChangesAsync();

        // Act
        var response = await _client.GetAsync($"/api/games/{game.Id}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var gameResult = await response.Content.ReadFromJsonAsync<Game>();
        gameResult.Should().NotBeNull();
        gameResult!.Id.Should().Be(game.Id);
        gameResult.Player1Id.Should().Be(game.Player1Id);
        gameResult.Player2Id.Should().Be(game.Player2Id);
    }

    [TestMethod]
    public async Task GET_ApiGamesById_ShouldReturn404ForNonExistentGame()
    {
        // Act
        var response = await _client.GetAsync($"/api/games/{Guid.NewGuid()}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        
        var content = await response.Content.ReadAsStringAsync();
        var jsonDoc = JsonDocument.Parse(content);
        jsonDoc.Should().NotBeNull("Error response should be valid JSON");
    }

    [TestMethod]
    public async Task POST_ApiGamesCreate_ShouldCreateNewGame()
    {
        // Arrange
        var createRequest = new
        {
            Player1Id = Guid.NewGuid(),
            Player2Id = Guid.NewGuid()
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games", createRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        
        var createdGame = await response.Content.ReadFromJsonAsync<Game>();
        createdGame.Should().NotBeNull();
        createdGame!.Player1Id.Should().Be(createRequest.Player1Id);
        createdGame.Player2Id.Should().Be(createRequest.Player2Id);
        createdGame.Status.Should().Be(GameStatus.WaitingForPlayers);
    }

    [TestMethod]
    public async Task POST_ApiGamesCreate_ShouldReturn400ForInvalidRequest()
    {
        // Arrange
        var invalidRequest = new
        {
            Player1Id = Guid.Empty, // Invalid GUID
            Player2Id = Guid.Empty  // Invalid GUID
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games", invalidRequest);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        
        var content = await response.Content.ReadAsStringAsync();
        var jsonDoc = JsonDocument.Parse(content);
        jsonDoc.Should().NotBeNull("Error response should be valid JSON");
    }

    [TestMethod]
    public async Task PUT_ApiGamesStart_ShouldStartGame()
    {
        // Arrange
        var game = CreateTestGame();
        await _dbContext.Games.AddAsync(game);
        await _dbContext.SaveChangesAsync();

        // Act
        var response = await _client.PutAsync($"/api/games/{game.Id}/start", null);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var updatedGame = await response.Content.ReadFromJsonAsync<Game>();
        updatedGame.Should().NotBeNull();
        updatedGame!.Status.Should().Be(GameStatus.InProgress);
        updatedGame.StartTime.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromMinutes(1));
    }

    [TestMethod]
    public async Task POST_ApiGamesSubmitAnswer_ShouldProcessAnswer()
    {
        // Arrange
        var game = CreateTestGame();
        game.Status = GameStatus.InProgress;
        await _dbContext.Games.AddAsync(game);
        await _dbContext.SaveChangesAsync();

        var submitRequest = new
        {
            GameId = game.Id,
            PlayerId = game.Player1Id,
            Answer = "HELLO",
            RoundType = "letters"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/submit-answer", submitRequest);

        // Assert
        response.StatusCode.Should().BeOneOf(HttpStatusCode.OK, HttpStatusCode.Accepted);
        
        var content = await response.Content.ReadAsStringAsync();
        var jsonDoc = JsonDocument.Parse(content);
        jsonDoc.Should().NotBeNull("Response should be valid JSON");
    }

    [TestMethod]
    public async Task GET_ApiLeaderboard_ShouldReturnTopPlayers()
    {
        // Act
        var response = await _client.GetAsync("/api/leaderboard");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var leaderboard = await response.Content.ReadFromJsonAsync<List<object>>();
        leaderboard.Should().NotBeNull();
    }

    [TestMethod]
    public async Task GET_ApiLeaderboardWithLimit_ShouldRespectLimit()
    {
        // Act
        var response = await _client.GetAsync("/api/leaderboard?limit=5");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var leaderboard = await response.Content.ReadFromJsonAsync<List<object>>();
        leaderboard.Should().NotBeNull();
        leaderboard!.Count.Should().BeLessOrEqualTo(5);
    }

    [TestMethod]
    public async Task GET_ApiStats_ShouldReturnGameStatistics()
    {
        // Act
        var response = await _client.GetAsync("/api/stats");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var stats = await response.Content.ReadFromJsonAsync<object>();
        stats.Should().NotBeNull();
        
        var content = await response.Content.ReadAsStringAsync();
        content.Should().Contain("totalGames", "Stats should include total games");
    }

    [TestMethod]
    public async Task GET_ApiHealth_ShouldReturnHealthStatus()
    {
        // Act
        var response = await _client.GetAsync("/health");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        
        var content = await response.Content.ReadAsStringAsync();
        content.Should().NotBeNullOrEmpty();
        
        // Should be valid JSON
        var jsonDoc = JsonDocument.Parse(content);
        jsonDoc.Should().NotBeNull();
    }

    [TestMethod]
    public async Task DELETE_ApiGamesById_ShouldDeleteGame()
    {
        // Arrange
        var game = CreateTestGame();
        await _dbContext.Games.AddAsync(game);
        await _dbContext.SaveChangesAsync();

        // Act
        var response = await _client.DeleteAsync($"/api/games/{game.Id}");

        // Assert
        response.StatusCode.Should().BeOneOf(HttpStatusCode.OK, HttpStatusCode.NoContent);
        
        // Verify game is deleted
        var getResponse = await _client.GetAsync($"/api/games/{game.Id}");
        getResponse.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [TestMethod]
    public async Task AllEndpoints_ShouldReturnValidJson_NotHtml()
    {
        // Test that all endpoints return JSON, not HTML error pages
        var endpoints = new[]
        {
            "/api/games",
            "/api/leaderboard",
            "/api/stats",
            "/health",
            $"/api/games/{Guid.NewGuid()}", // This will 404 but should be JSON
        };

        foreach (var endpoint in endpoints)
        {
            // Act
            var response = await _client.GetAsync(endpoint);

            // Assert
            var content = await response.Content.ReadAsStringAsync();
            content.Should().NotBeNullOrEmpty($"Endpoint {endpoint} should return content");
            
            // Should not be HTML
            content.Should().NotContain("<html>", $"Endpoint {endpoint} should not return HTML");
            content.Should().NotContain("<!DOCTYPE", $"Endpoint {endpoint} should not return HTML");
            
            // Should be valid JSON (or at least attempt to parse)
            try
            {
                JsonDocument.Parse(content);
            }
            catch (JsonException)
            {
                Assert.Fail($"Endpoint {endpoint} returned invalid JSON: {content}");
            }
        }
    }

    [TestMethod]
    public async Task Performance_ApiEndpoints_ShouldRespondQuickly()
    {
        // Test that API endpoints respond within performance requirements (<200ms)
        var endpoints = new[]
        {
            "/api/games",
            "/api/leaderboard",
            "/api/stats",
            "/health"
        };

        foreach (var endpoint in endpoints)
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            
            // Act
            var response = await _client.GetAsync(endpoint);
            
            stopwatch.Stop();

            // Assert
            response.StatusCode.Should().Be(HttpStatusCode.OK, $"Endpoint {endpoint} should respond successfully");
            stopwatch.ElapsedMilliseconds.Should().BeLessThan(200, 
                $"Endpoint {endpoint} should respond within 200ms (actual: {stopwatch.ElapsedMilliseconds}ms)");
        }
    }

    [TestMethod]
    public async Task API_ShouldHandleConcurrentRequests()
    {
        // Test concurrent request handling
        var tasks = new List<Task<HttpResponseMessage>>();
        
        // Create multiple concurrent requests
        for (int i = 0; i < 20; i++)
        {
            tasks.Add(_client.GetAsync("/api/games"));
        }

        // Act
        var responses = await Task.WhenAll(tasks);

        // Assert
        responses.Should().HaveCount(20);
        responses.Should().OnlyContain(r => r.StatusCode == HttpStatusCode.OK, 
            "All concurrent requests should succeed");

        // Verify all responses are valid JSON
        foreach (var response in responses)
        {
            var content = await response.Content.ReadAsStringAsync();
            JsonDocument.Parse(content); // Should not throw
        }
    }

    [TestMethod]
    public async Task API_ShouldHandleInvalidHttpMethods()
    {
        // Test that endpoints properly handle invalid HTTP methods
        var invalidMethods = new[]
        {
            new { Method = HttpMethod.Patch, Endpoint = "/api/games" },
            new { Method = HttpMethod.Put, Endpoint = "/api/leaderboard" },
            new { Method = HttpMethod.Delete, Endpoint = "/api/stats" }
        };

        foreach (var test in invalidMethods)
        {
            var request = new HttpRequestMessage(test.Method, test.Endpoint);
            
            // Act
            var response = await _client.SendAsync(request);

            // Assert
            response.StatusCode.Should().Be(HttpStatusCode.MethodNotAllowed,
                $"Endpoint {test.Endpoint} should not allow {test.Method}");
        }
    }

    [TestMethod]
    public async Task API_ShouldIncludeProperHeaders()
    {
        // Act
        var response = await _client.GetAsync("/api/games");

        // Assert
        response.Headers.Should().ContainKey("Content-Type");
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/json");
        
        // Check for security headers (if implemented)
        if (response.Headers.Contains("X-Content-Type-Options"))
        {
            response.Headers.GetValues("X-Content-Type-Options").Should().Contain("nosniff");
        }
    }

    private static Game CreateTestGame()
    {
        return new Game
        {
            Id = Guid.NewGuid(),
            Player1Id = Guid.NewGuid(),
            Player2Id = Guid.NewGuid(),
            Status = GameStatus.WaitingForPlayers,
            CurrentRound = 1,
            Player1Score = 0,
            Player2Score = 0,
            CreatedAt = DateTime.UtcNow
        };
    }

    private void SeedTestData()
    {
        // Add some test data to the database
        var testGames = new List<Game>();
        
        for (int i = 0; i < 3; i++)
        {
            testGames.Add(CreateTestGame());
        }

        _dbContext.Games.AddRange(testGames);
        _dbContext.SaveChanges();
    }
}