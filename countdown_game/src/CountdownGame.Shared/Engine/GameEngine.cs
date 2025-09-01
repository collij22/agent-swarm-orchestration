using CountdownGame.Shared.Models;
using CountdownGame.Shared.Services;
using Microsoft.Extensions.Logging;

namespace CountdownGame.Shared.Engine;

public class GameEngine
{
    private readonly ILogger<GameEngine> _logger;
    private readonly DictionaryService _dictionaryService;
    private readonly NumbersSolver _numbersSolver;
    private readonly Random _random = new();

    public GameEngine(ILogger<GameEngine> logger, DictionaryService dictionaryService, NumbersSolver numbersSolver)
    {
        _logger = logger;
        _dictionaryService = dictionaryService;
        _numbersSolver = numbersSolver;
    }

    public GameSession CreateGame(GameMode mode, string hostPlayerId, string hostPlayerName)
    {
        var game = new GameSession
        {
            Id = Guid.NewGuid().ToString(),
            Mode = mode,
            State = GameState.WaitingForPlayers,
            InviteCode = mode == GameMode.Multiplayer ? GenerateInviteCode() : null
        };

        var hostPlayer = new Player
        {
            Id = hostPlayerId,
            Name = hostPlayerName
        };
        
        game.Players.Add(hostPlayer);
        game.CurrentPlayer = hostPlayer;

        // Generate rounds for the game
        GenerateRounds(game);

        _logger.LogInformation("Created game {GameId} for player {PlayerId}", game.Id, hostPlayerId);
        return game;
    }

    public void AddAIPlayer(GameSession game, AIDifficulty difficulty)
    {
        var aiPlayer = new Player
        {
            Id = Guid.NewGuid().ToString(),
            Name = $"AI ({difficulty})",
            IsAI = true,
            AIDifficulty = difficulty
        };

        game.Players.Add(aiPlayer);
        _logger.LogInformation("Added AI player to game {GameId}", game.Id);
    }

    public bool JoinGame(GameSession game, string playerId, string playerName)
    {
        if (game.Players.Count >= 2 || game.State != GameState.WaitingForPlayers)
            return false;

        var player = new Player
        {
            Id = playerId,
            Name = playerName
        };

        game.Players.Add(player);
        _logger.LogInformation("Player {PlayerId} joined game {GameId}", playerId, game.Id);
        return true;
    }

    public void StartGame(GameSession game)
    {
        if (game.Players.Count < 2)
            throw new InvalidOperationException("Cannot start game with less than 2 players");

        game.State = GameState.InProgress;
        game.StartedAt = DateTime.UtcNow;
        game.CurrentRoundIndex = 0;
        
        StartRound(game);
        _logger.LogInformation("Started game {GameId}", game.Id);
    }

    public void StartRound(GameSession game)
    {
        var round = game.CurrentRound;
        if (round == null) return;

        round.StartedAt = DateTime.UtcNow;
        game.State = GameState.RoundInProgress;

        // Set current player (alternates each round)
        var currentPlayerIndex = game.CurrentRoundIndex % game.Players.Count;
        game.CurrentPlayer = game.Players[currentPlayerIndex];

        _logger.LogInformation("Started round {RoundNumber} ({RoundType}) in game {GameId}", 
            round.Number, round.Type, game.Id);
    }

    public async Task<RoundResult> SubmitAnswer(GameSession game, string playerId, string answer, string? expression = null)
    {
        var round = game.CurrentRound;
        if (round == null || !round.StartedAt.HasValue)
            throw new InvalidOperationException("No active round");

        var result = new RoundResult
        {
            PlayerId = playerId,
            Answer = answer,
            SubmittedAt = DateTime.UtcNow,
            Expression = expression
        };

        // Validate and score based on round type
        switch (round.Type)
        {
            case RoundType.Letters:
                await ValidateLettersAnswer(result, round);
                break;
            case RoundType.Numbers:
                ValidateNumbersAnswer(result, round);
                break;
            case RoundType.Conundrum:
                ValidateConundrumAnswer(result, round);
                break;
        }

        round.PlayerResults[playerId] = result;
        
        // Check if round is complete
        if (ShouldCompleteRound(game, round))
        {
            CompleteRound(game, round);
        }

        return result;
    }

    private async Task ValidateLettersAnswer(RoundResult result, Round round)
    {
        if (string.IsNullOrWhiteSpace(result.Answer) || round.SelectedLetters == null)
        {
            result.IsValid = false;
            result.ValidationMessage = "Invalid answer";
            return;
        }

        var answer = result.Answer.ToUpper();
        
        // Check if word can be made from selected letters
        var letterCounts = round.SelectedLetters.GroupBy(c => c).ToDictionary(g => g.Key, g => g.Count());
        var answerCounts = answer.GroupBy(c => c).ToDictionary(g => g.Key, g => g.Count());

        foreach (var kvp in answerCounts)
        {
            if (!letterCounts.ContainsKey(kvp.Key) || letterCounts[kvp.Key] < kvp.Value)
            {
                result.IsValid = false;
                result.ValidationMessage = "Word cannot be made from selected letters";
                return;
            }
        }

        // Check dictionary
        result.IsValid = await _dictionaryService.IsValidWordAsync(answer);
        if (result.IsValid)
        {
            result.Score = answer.Length;
            if (answer.Length == 9) result.Score = 18; // Bonus for 9-letter word
        }
        else
        {
            result.ValidationMessage = "Word not found in dictionary";
        }
    }

    private void ValidateNumbersAnswer(RoundResult result, Round round)
    {
        if (string.IsNullOrWhiteSpace(result.Expression) || 
            round.SelectedNumbers == null || !round.Target.HasValue)
        {
            result.IsValid = false;
            result.ValidationMessage = "Invalid expression";
            return;
        }

        try
        {
            var calculatedResult = _numbersSolver.EvaluateExpression(result.Expression, round.SelectedNumbers);
            result.CalculatedResult = calculatedResult;
            
            var difference = Math.Abs(calculatedResult - round.Target.Value);
            result.IsValid = true;
            
            // Scoring: 10 points for exact, 7 for within 5, 5 for within 10
            if (difference == 0) result.Score = 10;
            else if (difference <= 5) result.Score = 7;
            else if (difference <= 10) result.Score = 5;
            else result.Score = 0;
        }
        catch (Exception ex)
        {
            result.IsValid = false;
            result.ValidationMessage = ex.Message;
        }
    }

    private void ValidateConundrumAnswer(RoundResult result, Round round)
    {
        if (string.IsNullOrWhiteSpace(result.Answer) || string.IsNullOrWhiteSpace(round.ConundrumWord))
        {
            result.IsValid = false;
            result.ValidationMessage = "Invalid answer";
            return;
        }

        result.IsValid = string.Equals(result.Answer, round.ConundrumWord, StringComparison.OrdinalIgnoreCase);
        result.Score = result.IsValid ? 10 : 0;
        
        if (!result.IsValid)
        {
            result.ValidationMessage = $"Incorrect. The answer was: {round.ConundrumWord}";
        }
    }

    private bool ShouldCompleteRound(GameSession game, Round round)
    {
        // For conundrum, complete immediately after first correct answer
        if (round.Type == RoundType.Conundrum)
        {
            return round.PlayerResults.Values.Any(r => r.IsValid);
        }

        // For other rounds, wait for all players or timeout
        var activePlayersCount = game.Players.Count(p => !p.IsAI || p.IsAI);
        return round.PlayerResults.Count >= activePlayersCount;
    }

    private void CompleteRound(GameSession game, Round round)
    {
        round.CompletedAt = DateTime.UtcNow;
        game.State = GameState.RoundComplete;

        // Update player scores
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
            CompleteGame(game);
        }
        else
        {
            game.CurrentRoundIndex++;
            // Auto-start next round after brief delay in real implementation
        }

        _logger.LogInformation("Completed round {RoundNumber} in game {GameId}", 
            round.Number, game.Id);
    }

    private void CompleteGame(GameSession game)
    {
        game.State = GameState.GameComplete;
        game.CompletedAt = DateTime.UtcNow;

        var winner = game.Players.OrderByDescending(p => p.Score).First();
        _logger.LogInformation("Game {GameId} completed. Winner: {PlayerId} with score {Score}", 
            game.Id, winner.Id, winner.Score);
    }

    private void GenerateRounds(GameSession game)
    {
        game.Rounds.Clear();

        // Generate 10 letters rounds
        for (int i = 1; i <= 10; i++)
        {
            game.Rounds.Add(new Round
            {
                Number = i,
                Type = RoundType.Letters,
                SelectedLetters = GenerateRandomLetters()
            });
        }

        // Generate 4 numbers rounds
        for (int i = 11; i <= 14; i++)
        {
            var numbers = GenerateRandomNumbers();
            game.Rounds.Add(new Round
            {
                Number = i,
                Type = RoundType.Numbers,
                SelectedNumbers = numbers,
                Target = GenerateTarget()
            });
        }

        // Generate 1 conundrum round
        var conundrum = GenerateConundrum();
        game.Rounds.Add(new Round
        {
            Number = 15,
            Type = RoundType.Conundrum,
            ConundrumWord = conundrum.word,
            ScrambledWord = conundrum.scrambled
        });
    }

    private List<char> GenerateRandomLetters()
    {
        var letters = new List<char>();
        var vowelCount = _random.Next(3, 6); // 3-5 vowels
        var consonantCount = 9 - vowelCount;

        // Add random vowels
        for (int i = 0; i < vowelCount; i++)
        {
            letters.Add(LettersConstraints.Vowels[_random.Next(LettersConstraints.Vowels.Length)]);
        }

        // Add random consonants
        for (int i = 0; i < consonantCount; i++)
        {
            letters.Add(LettersConstraints.Consonants[_random.Next(LettersConstraints.Consonants.Length)]);
        }

        return letters.OrderBy(x => _random.Next()).ToList();
    }

    private List<int> GenerateRandomNumbers()
    {
        var numbers = new List<int>();
        var largeCount = _random.Next(0, 3); // 0-2 large numbers
        var smallCount = 6 - largeCount;

        // Add large numbers
        var availableLarge = NumbersConstraints.LargeNumbers.ToList();
        for (int i = 0; i < largeCount; i++)
        {
            var index = _random.Next(availableLarge.Count);
            numbers.Add(availableLarge[index]);
            availableLarge.RemoveAt(index);
        }

        // Add small numbers
        var availableSmall = NumbersConstraints.SmallNumbers.ToList();
        for (int i = 0; i < smallCount; i++)
        {
            var index = _random.Next(availableSmall.Count);
            numbers.Add(availableSmall[index]);
            availableSmall.RemoveAt(index);
        }

        return numbers.OrderBy(x => _random.Next()).ToList();
    }

    private int GenerateTarget()
    {
        return _random.Next(NumbersConstraints.MinTarget, NumbersConstraints.MaxTarget + 1);
    }

    private (string word, string scrambled) GenerateConundrum()
    {
        // Simplified - in real implementation would use curated database
        var words = new[] { "COUNTDOWN", "CHALLENGE", "SOLUTIONS", "ALGORITHM", "FRAMEWORK" };
        var word = words[_random.Next(words.Length)];
        var scrambled = new string(word.OrderBy(x => _random.Next()).ToArray());
        return (word, scrambled);
    }

    private string GenerateInviteCode()
    {
        const string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        return new string(Enumerable.Repeat(chars, 6)
            .Select(s => s[_random.Next(s.Length)]).ToArray());
    }
}