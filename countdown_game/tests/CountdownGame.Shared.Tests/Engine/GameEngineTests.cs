using CountdownGame.Shared.Engine;
using CountdownGame.Shared.Models;
using FluentAssertions;
using Moq;
using Xunit;

namespace CountdownGame.Shared.Tests.Engine;

public class GameEngineTests
{
    private readonly GameEngine _gameEngine;

    public GameEngineTests()
    {
        _gameEngine = new GameEngine();
    }

    [Fact]
    public void CreateNewGame_ShouldInitializeWithCorrectDefaults()
    {
        // Act
        var game = _gameEngine.CreateNewGame("player1", "player2");

        // Assert
        game.Should().NotBeNull();
        game.CurrentRound.Should().Be(1);
        game.Status.Should().Be(GameStatus.WaitingForPlayers);
        game.Player1.Name.Should().Be("player1");
        game.Player2.Name.Should().Be("player2");
        game.Player1.Score.Should().Be(0);
        game.Player2.Score.Should().Be(0);
        game.Rounds.Should().HaveCount(15);
    }

    [Fact]
    public void StartGame_ShouldTransitionToInProgress()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");

        // Act
        _gameEngine.StartGame(game);

        // Assert
        game.Status.Should().Be(GameStatus.InProgress);
        game.StartTime.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
    }

    [Theory]
    [InlineData(1, RoundType.Letters)]
    [InlineData(2, RoundType.Letters)]
    [InlineData(3, RoundType.Numbers)]
    [InlineData(6, RoundType.Numbers)]
    [InlineData(9, RoundType.Numbers)]
    [InlineData(12, RoundType.Numbers)]
    [InlineData(15, RoundType.Conundrum)]
    public void GetRoundType_ShouldReturnCorrectTypeForRoundNumber(int roundNumber, RoundType expectedType)
    {
        // Act
        var roundType = _gameEngine.GetRoundType(roundNumber);

        // Assert
        roundType.Should().Be(expectedType);
    }

    [Fact]
    public void GenerateLettersSelection_ShouldHave9Letters()
    {
        // Act
        var letters = _gameEngine.GenerateLettersSelection();

        // Assert
        letters.Should().HaveCount(9);
        letters.Should().OnlyContain(c => char.IsLetter(c));
    }

    [Fact]
    public void GenerateLettersSelection_ShouldHaveValidVowelConsonantRatio()
    {
        // Act
        var letters = _gameEngine.GenerateLettersSelection();

        // Assert
        var vowels = letters.Count(c => "AEIOU".Contains(char.ToUpper(c)));
        var consonants = letters.Count(c => !"AEIOU".Contains(char.ToUpper(c)));

        vowels.Should().BeGreaterOrEqualTo(3);
        consonants.Should().BeGreaterOrEqualTo(4);
        (vowels + consonants).Should().Be(9);
    }

    [Fact]
    public void GenerateNumbersSelection_ShouldHave6Numbers()
    {
        // Act
        var numbers = _gameEngine.GenerateNumbersSelection();

        // Assert
        numbers.Should().HaveCount(6);
        numbers.Should().OnlyContain(n => n > 0);
    }

    [Fact]
    public void GenerateNumbersSelection_ShouldFollowSmallLargeNumberRules()
    {
        // Act
        var numbers = _gameEngine.GenerateNumbersSelection();

        // Assert
        var smallNumbers = numbers.Where(n => n <= 10).ToList();
        var largeNumbers = numbers.Where(n => n > 10).ToList();

        // Should have mix of small and large numbers
        smallNumbers.Should().NotBeEmpty();
        largeNumbers.Should().NotBeEmpty();

        // Large numbers should only be from the allowed set
        var allowedLargeNumbers = new[] { 25, 50, 75, 100 };
        largeNumbers.Should().OnlyContain(n => allowedLargeNumbers.Contains(n));
    }

    [Fact]
    public void GenerateTarget_ShouldBeInValidRange()
    {
        // Act
        var target = _gameEngine.GenerateTarget();

        // Assert
        target.Should().BeInRange(100, 999);
    }

    [Theory]
    [InlineData("HELLO", 5)]
    [InlineData("TESTING", 7)]
    [InlineData("COUNTDOWN", 9)]
    public void ScoreLettersRound_ShouldCalculateCorrectScore(string word, int expectedScore)
    {
        // Act
        var score = _gameEngine.ScoreLettersRound(word, new[] { 'C', 'O', 'U', 'N', 'T', 'D', 'O', 'W', 'N' });

        // Assert
        if (word.Length <= 9)
        {
            score.Should().Be(expectedScore);
        }
    }

    [Fact]
    public void ScoreLettersRound_ShouldGive18PointsFor9LetterWord()
    {
        // Arrange
        var letters = new[] { 'C', 'O', 'U', 'N', 'T', 'D', 'O', 'W', 'N' };
        var nineLetterWord = "COUNTDOWN";

        // Act
        var score = _gameEngine.ScoreLettersRound(nineLetterWord, letters);

        // Assert
        score.Should().Be(18);
    }

    [Theory]
    [InlineData(0, 10)] // Exact match
    [InlineData(1, 7)]  // Within 1
    [InlineData(5, 7)]  // Within 5
    [InlineData(6, 5)]  // Within 6-10
    [InlineData(10, 5)] // Within 6-10
    [InlineData(11, 0)] // More than 10 away
    public void ScoreNumbersRound_ShouldCalculateCorrectScore(int difference, int expectedScore)
    {
        // Arrange
        var target = 500;
        var result = target + difference;

        // Act
        var score = _gameEngine.ScoreNumbersRound(result, target);

        // Assert
        score.Should().Be(expectedScore);
    }

    [Fact]
    public void ScoreConundrumRound_ShouldGive10PointsForCorrectAnswer()
    {
        // Act
        var score = _gameEngine.ScoreConundrumRound(true);

        // Assert
        score.Should().Be(10);
    }

    [Fact]
    public void ScoreConundrumRound_ShouldGive0PointsForIncorrectAnswer()
    {
        // Act
        var score = _gameEngine.ScoreConundrumRound(false);

        // Assert
        score.Should().Be(0);
    }

    [Fact]
    public void SubmitLettersAnswer_ShouldUpdatePlayerScore()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        _gameEngine.StartGame(game);
        var letters = _gameEngine.GenerateLettersSelection();
        game.Rounds[0].Letters = letters;

        // Act
        _gameEngine.SubmitLettersAnswer(game, game.Player1.Id, "HELLO", letters);

        // Assert
        game.Player1.Score.Should().BeGreaterThan(0);
    }

    [Fact]
    public void SubmitNumbersAnswer_ShouldUpdatePlayerScore()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        _gameEngine.StartGame(game);
        var numbers = new[] { 1, 2, 3, 4, 5, 6 };
        var target = 10;
        game.Rounds[2].Numbers = numbers; // Round 3 is a numbers round
        game.Rounds[2].Target = target;

        // Act
        _gameEngine.SubmitNumbersAnswer(game, game.Player1.Id, 10, "1 + 2 + 3 + 4");

        // Assert
        game.Player1.Score.Should().BeGreaterThan(0);
    }

    [Fact]
    public void NextRound_ShouldAdvanceToNextRound()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        _gameEngine.StartGame(game);

        // Act
        _gameEngine.NextRound(game);

        // Assert
        game.CurrentRound.Should().Be(2);
    }

    [Fact]
    public void NextRound_ShouldCompleteGameAfterRound15()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        _gameEngine.StartGame(game);
        game.CurrentRound = 15;

        // Act
        _gameEngine.NextRound(game);

        // Assert
        game.Status.Should().Be(GameStatus.Completed);
        game.EndTime.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(1));
    }

    [Fact]
    public void DetermineWinner_ShouldReturnPlayerWithHighestScore()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        game.Player1.Score = 50;
        game.Player2.Score = 30;

        // Act
        var winner = _gameEngine.DetermineWinner(game);

        // Assert
        winner.Should().Be(game.Player1);
    }

    [Fact]
    public void DetermineWinner_ShouldReturnNullForTie()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");
        game.Player1.Score = 50;
        game.Player2.Score = 50;

        // Act
        var winner = _gameEngine.DetermineWinner(game);

        // Assert
        winner.Should().BeNull();
    }

    [Fact]
    public void IsValidLettersWord_ShouldValidateWordAgainstAvailableLetters()
    {
        // Arrange
        var letters = new[] { 'H', 'E', 'L', 'L', 'O', 'W', 'O', 'R', 'D' };

        // Act & Assert
        _gameEngine.IsValidLettersWord("HELLO", letters).Should().BeTrue();
        _gameEngine.IsValidLettersWord("WORLD", letters).Should().BeTrue();
        _gameEngine.IsValidLettersWord("INVALID", letters).Should().BeFalse();
    }

    [Theory]
    [InlineData("")]
    [InlineData("A")]
    [InlineData("TOOLONGWORD")]
    public void IsValidLettersWord_ShouldRejectInvalidLengths(string word)
    {
        // Arrange
        var letters = new[] { 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I' };

        // Act
        var isValid = _gameEngine.IsValidLettersWord(word, letters);

        // Assert
        isValid.Should().BeFalse();
    }

    [Fact]
    public void GetCurrentPlayer_ShouldAlternateBasedOnRound()
    {
        // Arrange
        var game = _gameEngine.CreateNewGame("player1", "player2");

        // Act & Assert
        for (int round = 1; round <= 15; round++)
        {
            game.CurrentRound = round;
            var currentPlayer = _gameEngine.GetCurrentPlayer(game);
            
            // Player 1 starts odd rounds, Player 2 starts even rounds
            if (round % 2 == 1)
            {
                currentPlayer.Should().Be(game.Player1);
            }
            else
            {
                currentPlayer.Should().Be(game.Player2);
            }
        }
    }
}