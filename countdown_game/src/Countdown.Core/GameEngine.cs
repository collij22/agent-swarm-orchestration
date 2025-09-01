using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Countdown.Core
{
    /// <summary>
    /// Core game engine that manages the Countdown game flow
    /// </summary>
    public class GameEngine
    {
        private readonly List<IRound> _rounds;
        private readonly IScoreKeeper _scoreKeeper;
        private readonly ITimeKeeper _timeKeeper;
        private readonly IRoundFactory _roundFactory;
        
        private GameState _currentGame;
        private int _currentRoundIndex;
        
        public event EventHandler<RoundStartedEventArgs> RoundStarted;
        public event EventHandler<RoundCompletedEventArgs> RoundCompleted;
        public event EventHandler<GameCompletedEventArgs> GameCompleted;
        
        public GameEngine(
            IScoreKeeper scoreKeeper,
            ITimeKeeper timeKeeper,
            IRoundFactory roundFactory)
        {
            _scoreKeeper = scoreKeeper;
            _timeKeeper = timeKeeper;
            _roundFactory = roundFactory;
            _rounds = new List<IRound>();
        }
        
        /// <summary>
        /// Initialize a new game with the standard 15-round format
        /// </summary>
        public async Task<GameState> StartNewGame(Player champion, Player challenger)
        {
            _currentGame = new GameState
            {
                GameId = Guid.NewGuid(),
                Champion = champion,
                Challenger = challenger,
                StartTime = DateTime.UtcNow,
                Status = GameStatus.InProgress
            };
            
            // Create the 15-round sequence as per TV format
            _rounds.Clear();
            _rounds.AddRange(CreateStandardRoundSequence());
            
            _currentRoundIndex = 0;
            _scoreKeeper.Reset();
            
            // Randomly assign who goes first
            var random = new Random();
            _currentGame.CurrentController = random.Next(2) == 0 ? champion : challenger;
            
            return _currentGame;
        }
        
        /// <summary>
        /// Execute the next round in the sequence
        /// </summary>
        public async Task<RoundResult> PlayNextRound()
        {
            if (_currentRoundIndex >= _rounds.Count)
            {
                throw new InvalidOperationException("All rounds have been played");
            }
            
            var round = _rounds[_currentRoundIndex];
            var roundNumber = _currentRoundIndex + 1;
            
            // Notify round is starting
            RoundStarted?.Invoke(this, new RoundStartedEventArgs
            {
                RoundNumber = roundNumber,
                RoundType = round.Type,
                Controller = _currentGame.CurrentController
            });
            
            // Start the 30-second timer
            _timeKeeper.StartTimer(30);
            
            // Execute the round
            var result = await round.Execute(_currentGame);
            
            // Update scores
            _scoreKeeper.UpdateScores(result);
            
            // Alternate control for next round
            _currentGame.CurrentController = _currentGame.CurrentController == _currentGame.Champion 
                ? _currentGame.Challenger 
                : _currentGame.Champion;
            
            // Notify round completed
            RoundCompleted?.Invoke(this, new RoundCompletedEventArgs
            {
                RoundNumber = roundNumber,
                Result = result,
                ChampionScore = _scoreKeeper.ChampionScore,
                ChallengerScore = _scoreKeeper.ChallengerScore
            });
            
            _currentRoundIndex++;
            
            // Check if game is complete
            if (_currentRoundIndex >= _rounds.Count)
            {
                await CompleteGame();
            }
            
            return result;
        }
        
        /// <summary>
        /// Create the standard 15-round sequence
        /// </summary>
        private List<IRound> CreateStandardRoundSequence()
        {
            var rounds = new List<IRound>();
            
            // Round order as per TV format
            var roundTypes = new[]
            {
                RoundType.Letters,   // 1
                RoundType.Letters,   // 2
                RoundType.Numbers,   // 3
                RoundType.Letters,   // 4
                RoundType.Numbers,   // 5
                RoundType.Letters,   // 6
                RoundType.Numbers,   // 7
                RoundType.Letters,   // 8
                RoundType.Numbers,   // 9
                RoundType.Letters,   // 10
                RoundType.Letters,   // 11
                RoundType.Letters,   // 12
                RoundType.Letters,   // 13
                RoundType.Numbers,   // 14
                RoundType.Conundrum  // 15
            };
            
            foreach (var type in roundTypes)
            {
                rounds.Add(_roundFactory.CreateRound(type));
            }
            
            return rounds;
        }
        
        /// <summary>
        /// Complete the game and determine winner
        /// </summary>
        private async Task CompleteGame()
        {
            _currentGame.EndTime = DateTime.UtcNow;
            _currentGame.Status = GameStatus.Completed;
            
            var championTotal = _scoreKeeper.ChampionScore;
            var challengerTotal = _scoreKeeper.ChallengerScore;
            
            if (championTotal == challengerTotal)
            {
                // Tie - need crucial conundrum
                _currentGame.Status = GameStatus.TieBreaker;
                await PlayCrucialConundrum();
            }
            else
            {
                _currentGame.Winner = championTotal > challengerTotal 
                    ? _currentGame.Champion 
                    : _currentGame.Challenger;
                
                GameCompleted?.Invoke(this, new GameCompletedEventArgs
                {
                    Game = _currentGame,
                    ChampionScore = championTotal,
                    ChallengerScore = challengerTotal,
                    Winner = _currentGame.Winner
                });
            }
        }
        
        /// <summary>
        /// Play sudden-death crucial conundrum for tie-breaking
        /// </summary>
        private async Task PlayCrucialConundrum()
        {
            var crucialConundrum = _roundFactory.CreateRound(RoundType.CrucialConundrum);
            
            RoundStarted?.Invoke(this, new RoundStartedEventArgs
            {
                RoundNumber = 16, // Special round
                RoundType = RoundType.CrucialConundrum,
                Controller = null // No controller in conundrum
            });
            
            var result = await crucialConundrum.Execute(_currentGame);
            
            if (result.ChampionScore > 0)
            {
                _currentGame.Winner = _currentGame.Champion;
            }
            else if (result.ChallengerScore > 0)
            {
                _currentGame.Winner = _currentGame.Challenger;
            }
            else
            {
                // Still tied, play another crucial conundrum
                await PlayCrucialConundrum();
                return;
            }
            
            GameCompleted?.Invoke(this, new GameCompletedEventArgs
            {
                Game = _currentGame,
                ChampionScore = _scoreKeeper.ChampionScore,
                ChallengerScore = _scoreKeeper.ChallengerScore,
                Winner = _currentGame.Winner,
                WasDecidedByCrucialConundrum = true
            });
        }
    }
    
    // Supporting interfaces and classes
    public interface IRound
    {
        RoundType Type { get; }
        Task<RoundResult> Execute(GameState gameState);
    }
    
    public interface IScoreKeeper
    {
        int ChampionScore { get; }
        int ChallengerScore { get; }
        void UpdateScores(RoundResult result);
        void Reset();
    }
    
    public interface ITimeKeeper
    {
        void StartTimer(int seconds);
        void StopTimer();
        event EventHandler<TimeExpiredEventArgs> TimeExpired;
        int RemainingSeconds { get; }
    }
    
    public interface IRoundFactory
    {
        IRound CreateRound(RoundType type);
    }
    
    public enum RoundType
    {
        Letters,
        Numbers,
        Conundrum,
        CrucialConundrum
    }
    
    public enum GameStatus
    {
        NotStarted,
        InProgress,
        TieBreaker,
        Completed
    }
    
    public class GameState
    {
        public Guid GameId { get; set; }
        public Player Champion { get; set; }
        public Player Challenger { get; set; }
        public Player CurrentController { get; set; }
        public Player Winner { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime? EndTime { get; set; }
        public GameStatus Status { get; set; }
        public List<RoundResult> RoundResults { get; set; } = new List<RoundResult>();
    }
    
    public class Player
    {
        public Guid Id { get; set; }
        public string Name { get; set; }
        public int EloRating { get; set; }
        public bool IsAI { get; set; }
        public AIDifficulty? AIDifficulty { get; set; }
    }
    
    public enum AIDifficulty
    {
        Easy,
        Medium,
        Hard
    }
    
    public class RoundResult
    {
        public RoundType Type { get; set; }
        public int RoundNumber { get; set; }
        public int ChampionScore { get; set; }
        public int ChallengerScore { get; set; }
        public string ChampionSubmission { get; set; }
        public string ChallengerSubmission { get; set; }
        public string BestPossibleSolution { get; set; }
    }
    
    // Event arguments
    public class RoundStartedEventArgs : EventArgs
    {
        public int RoundNumber { get; set; }
        public RoundType RoundType { get; set; }
        public Player Controller { get; set; }
    }
    
    public class RoundCompletedEventArgs : EventArgs
    {
        public int RoundNumber { get; set; }
        public RoundResult Result { get; set; }
        public int ChampionScore { get; set; }
        public int ChallengerScore { get; set; }
    }
    
    public class GameCompletedEventArgs : EventArgs
    {
        public GameState Game { get; set; }
        public int ChampionScore { get; set; }
        public int ChallengerScore { get; set; }
        public Player Winner { get; set; }
        public bool WasDecidedByCrucialConundrum { get; set; }
    }
    
    public class TimeExpiredEventArgs : EventArgs
    {
        public int ElapsedSeconds { get; set; }
    }
}