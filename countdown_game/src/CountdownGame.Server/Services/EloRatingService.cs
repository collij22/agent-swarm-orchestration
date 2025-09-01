namespace CountdownGame.Server.Services;

public class EloRatingService
{
    private readonly ILogger<EloRatingService> _logger;

    public EloRatingService(ILogger<EloRatingService> logger)
    {
        _logger = logger;
    }

    public (int newRating1, int newRating2) CalculateNewRatings(int rating1, int rating2, double score1)
    {
        // score1: 1 = player1 wins, 0 = player2 wins, 0.5 = draw
        var score2 = 1 - score1;

        var k1 = GetKFactor(rating1);
        var k2 = GetKFactor(rating2);

        var expected1 = GetExpectedScore(rating1, rating2);
        var expected2 = GetExpectedScore(rating2, rating1);

        var newRating1 = (int)Math.Round(rating1 + k1 * (score1 - expected1));
        var newRating2 = (int)Math.Round(rating2 + k2 * (score2 - expected2));

        // Ensure ratings don't go below minimum
        newRating1 = Math.Max(100, newRating1);
        newRating2 = Math.Max(100, newRating2);

        _logger.LogDebug("ELO calculation: P1({Rating1}) vs P2({Rating2}) -> P1({NewRating1}) P2({NewRating2})",
            rating1, rating2, newRating1, newRating2);

        return (newRating1, newRating2);
    }

    private int GetKFactor(int rating)
    {
        // Dynamic K-factor based on rating
        if (rating < 1200) return 40; // New players
        if (rating < 1600) return 30; // Intermediate players
        if (rating < 2000) return 20; // Advanced players
        return 15; // Expert players
    }

    private double GetExpectedScore(int ratingA, int ratingB)
    {
        return 1.0 / (1.0 + Math.Pow(10.0, (ratingB - ratingA) / 400.0));
    }

    public int GetInitialRating()
    {
        return 1500; // Standard starting rating
    }

    public string GetRatingCategory(int rating)
    {
        return rating switch
        {
            < 800 => "Beginner",
            < 1200 => "Novice",
            < 1600 => "Intermediate",
            < 2000 => "Advanced",
            < 2400 => "Expert",
            _ => "Master"
        };
    }

    public double GetWinProbability(int rating1, int rating2)
    {
        return GetExpectedScore(rating1, rating2);
    }
}