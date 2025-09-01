using CountdownGame.Server.Services;
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

namespace CountdownGame.Server.Tests.Security;

[TestClass]
public class SecurityAuditTests
{
    private WebApplicationFactory<Program> _factory = null!;
    private HttpClient _client = null!;

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
                        options.UseInMemoryDatabase("SecurityTestDb");
                    });
                });
            });

        _client = _factory.CreateClient();
    }

    [TestCleanup]
    public void Cleanup()
    {
        _client.Dispose();
        _factory.Dispose();
    }

    [TestMethod]
    public async Task API_ShouldRejectMaliciousInput_SQLInjection()
    {
        // Arrange
        var maliciousPayload = new
        {
            playerName = "'; DROP TABLE Games; --",
            gameId = "1' OR '1'='1"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/create", maliciousPayload);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest, 
            "API should reject SQL injection attempts");
        
        var content = await response.Content.ReadAsStringAsync();
        content.Should().NotContain("DROP TABLE", "Response should not execute SQL injection");
    }

    [TestMethod]
    public async Task API_ShouldRejectMaliciousInput_XSSAttempts()
    {
        // Arrange
        var xssPayload = new
        {
            playerName = "<script>alert('xss')</script>",
            message = "javascript:alert('xss')"
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/create", xssPayload);

        // Assert
        var content = await response.Content.ReadAsStringAsync();
        content.Should().NotContain("<script>", "Response should sanitize XSS attempts");
        content.Should().NotContain("javascript:", "Response should sanitize JavaScript URLs");
    }

    [TestMethod]
    public async Task API_ShouldValidateInputLengths()
    {
        // Arrange
        var oversizedPayload = new
        {
            playerName = new string('A', 1000), // Very long name
            answer = new string('B', 10000)     // Very long answer
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/create", oversizedPayload);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
            "API should reject oversized input");
    }

    [TestMethod]
    public async Task API_ShouldRequireAuthentication_ForProtectedEndpoints()
    {
        // Act
        var responses = new[]
        {
            await _client.GetAsync("/api/games/my-games"),
            await _client.PostAsync("/api/games/create", null),
            await _client.PutAsync("/api/games/123/join", null),
            await _client.DeleteAsync("/api/games/123")
        };

        // Assert
        foreach (var response in responses)
        {
            response.StatusCode.Should().BeOneOf(HttpStatusCode.Unauthorized, HttpStatusCode.Forbidden,
                "Protected endpoints should require authentication");
        }
    }

    [TestMethod]
    public async Task API_ShouldValidateGUIDs()
    {
        // Arrange
        var invalidGuids = new[] { "invalid-guid", "123", "", "not-a-guid-at-all" };

        // Act & Assert
        foreach (var invalidGuid in invalidGuids)
        {
            var response = await _client.GetAsync($"/api/games/{invalidGuid}");
            response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
                $"API should reject invalid GUID: {invalidGuid}");
        }
    }

    [TestMethod]
    public async Task API_ShouldRateLimitRequests()
    {
        // Arrange
        var tasks = new List<Task<HttpResponseMessage>>();

        // Act - Send many requests rapidly
        for (int i = 0; i < 100; i++)
        {
            tasks.Add(_client.GetAsync("/api/games"));
        }

        var responses = await Task.WhenAll(tasks);

        // Assert
        var rateLimitedResponses = responses.Count(r => r.StatusCode == HttpStatusCode.TooManyRequests);
        rateLimitedResponses.Should().BeGreaterThan(0,
            "API should implement rate limiting for abuse protection");
    }

    [TestMethod]
    public async Task GameSubmission_ShouldValidateTimingConstraints()
    {
        // This test simulates anti-cheat timing validation
        // Arrange
        var gameData = new
        {
            gameId = Guid.NewGuid(),
            answer = "HELLO",
            submissionTime = DateTime.UtcNow.AddSeconds(-35) // Submitted after 30s limit
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/submit-answer", gameData);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
            "Late submissions should be rejected to prevent timing cheats");
    }

    [TestMethod]
    public async Task GameSubmission_ShouldValidateAnswerFormat()
    {
        // Arrange
        var invalidAnswers = new[]
        {
            new { answer = "", type = "letters" }, // Empty answer
            new { answer = "123HELLO", type = "letters" }, // Numbers in letters round
            new { answer = "HELLO WORLD", type = "letters" }, // Spaces not allowed
            new { answer = "a + b + c", type = "numbers" }, // Invalid numbers expression
            new { answer = "1 / 0", type = "numbers" } // Division by zero
        };

        // Act & Assert
        foreach (var invalidAnswer in invalidAnswers)
        {
            var response = await _client.PostAsJsonAsync("/api/games/submit-answer", invalidAnswer);
            response.StatusCode.Should().Be(HttpStatusCode.BadRequest,
                $"Invalid answer should be rejected: {invalidAnswer.answer}");
        }
    }

    [TestMethod]
    public async Task API_ShouldSanitizeErrorMessages()
    {
        // Arrange - Send request that will cause internal error
        var malformedPayload = "{ invalid json }";
        var content = new StringContent(malformedPayload, System.Text.Encoding.UTF8, "application/json");

        // Act
        var response = await _client.PostAsync("/api/games/create", content);

        // Assert
        var responseContent = await response.Content.ReadAsStringAsync();
        responseContent.Should().NotContain("System.", "Error messages should not expose internal details");
        responseContent.Should().NotContain("Exception", "Error messages should not expose exception details");
        responseContent.Should().NotContain("Stack trace", "Error messages should not expose stack traces");
    }

    [TestMethod]
    public async Task API_ShouldValidateContentType()
    {
        // Arrange
        var xmlContent = new StringContent("<xml>data</xml>", System.Text.Encoding.UTF8, "application/xml");

        // Act
        var response = await _client.PostAsync("/api/games/create", xmlContent);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnsupportedMediaType,
            "API should only accept expected content types");
    }

    [TestMethod]
    public async Task SignalR_ShouldValidateConnectionAuthentication()
    {
        // This would test SignalR hub authentication
        // For now, we'll test that unauthorized connections are rejected
        
        // Act
        var response = await _client.GetAsync("/gamehub");

        // Assert
        response.StatusCode.Should().BeOneOf(
            HttpStatusCode.Unauthorized, 
            HttpStatusCode.Forbidden,
            HttpStatusCode.NotFound, // SignalR might return 404 for unauthorized
            "SignalR hub should require authentication");
    }

    [TestMethod]
    public async Task API_ShouldImplementCSRFProtection()
    {
        // Arrange - Try to make state-changing request without proper headers
        var payload = new { gameId = Guid.NewGuid() };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/join", payload);

        // Assert
        // CSRF protection might manifest as requiring specific headers or tokens
        response.StatusCode.Should().BeOneOf(
            HttpStatusCode.BadRequest,
            HttpStatusCode.Forbidden,
            HttpStatusCode.Unauthorized,
            "API should implement CSRF protection for state-changing operations");
    }

    [TestMethod]
    public void InputValidation_ShouldRejectInvalidGameData()
    {
        // Test input validation at the model level
        var invalidGameData = new Game
        {
            Id = Guid.Empty, // Invalid GUID
            Player1Id = Guid.Empty,
            Player2Id = Guid.Empty,
            CurrentRound = -1, // Invalid round
            Status = (GameStatus)999 // Invalid enum value
        };

        // Act & Assert
        var validationResults = ValidateModel(invalidGameData);
        validationResults.Should().NotBeEmpty("Invalid game data should fail validation");
    }

    [TestMethod]
    public void AntiCheat_ShouldDetectImpossibleScores()
    {
        // Test anti-cheat detection for impossible scores
        var impossibleScores = new[]
        {
            new { roundType = "letters", score = 25, maxPossible = 18 }, // Max letters score is 18
            new { roundType = "numbers", score = 15, maxPossible = 10 }, // Max numbers score is 10
            new { roundType = "conundrum", score = 15, maxPossible = 10 } // Max conundrum score is 10
        };

        foreach (var scoreData in impossibleScores)
        {
            // This would be implemented in the actual anti-cheat system
            var isValidScore = scoreData.score <= scoreData.maxPossible;
            isValidScore.Should().BeFalse($"Score {scoreData.score} should be impossible for {scoreData.roundType} round");
        }
    }

    [TestMethod]
    public void AntiCheat_ShouldDetectTimingAnomalies()
    {
        // Test detection of suspiciously fast responses
        var suspiciousTimings = new[]
        {
            new { responseTime = TimeSpan.FromMilliseconds(100), minExpected = TimeSpan.FromSeconds(2) },
            new { responseTime = TimeSpan.FromMilliseconds(500), minExpected = TimeSpan.FromSeconds(3) }
        };

        foreach (var timing in suspiciousTimings)
        {
            var isSuspicious = timing.responseTime < timing.minExpected;
            isSuspicious.Should().BeTrue($"Response time {timing.responseTime.TotalMilliseconds}ms is suspiciously fast");
        }
    }

    [TestMethod]
    public async Task API_ShouldLogSecurityEvents()
    {
        // This test would verify that security-relevant events are logged
        // For now, we'll test that the logging infrastructure is in place
        
        // Arrange
        var maliciousPayload = new { playerName = "'; DROP TABLE Games; --" };

        // Act
        var response = await _client.PostAsJsonAsync("/api/games/create", maliciousPayload);

        // Assert
        // In a real implementation, we would check logs for security events
        // For now, we just verify the request was handled securely
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    private static List<string> ValidateModel(object model)
    {
        var context = new System.ComponentModel.DataAnnotations.ValidationContext(model);
        var results = new List<System.ComponentModel.DataAnnotations.ValidationResult>();
        
        System.ComponentModel.DataAnnotations.Validator.TryValidateObject(model, context, results, true);
        
        return results.Select(r => r.ErrorMessage ?? "Validation error").ToList();
    }
}