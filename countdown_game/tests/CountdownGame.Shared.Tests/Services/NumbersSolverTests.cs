using CountdownGame.Shared.Services;
using FluentAssertions;
using Xunit;

namespace CountdownGame.Shared.Tests.Services;

public class NumbersSolverTests
{
    private readonly NumbersSolver _numbersSolver;

    public NumbersSolverTests()
    {
        _numbersSolver = new NumbersSolver();
    }

    [Theory]
    [InlineData(new[] { 1, 2, 3, 4, 5, 6 }, 10)]
    [InlineData(new[] { 25, 50, 75, 100, 3, 6 }, 952)]
    [InlineData(new[] { 1, 1, 2, 2, 3, 3 }, 18)]
    public void FindSolutions_ShouldFindValidSolutions(int[] numbers, int target)
    {
        // Act
        var solutions = _numbersSolver.FindSolutions(numbers, target);

        // Assert
        solutions.Should().NotBeEmpty($"Should find at least one solution for target {target}");
        
        foreach (var solution in solutions.Take(5)) // Test first 5 solutions
        {
            solution.Should().NotBeNullOrEmpty("Solution expression should not be empty");
            var result = EvaluateExpression(solution);
            result.Should().Be(target, $"Expression '{solution}' should evaluate to {target}");
        }
    }

    [Fact]
    public void FindSolutions_ShouldReturnEmptyForImpossibleTarget()
    {
        // Arrange
        var numbers = new[] { 1, 1, 1, 1, 1, 1 };
        var impossibleTarget = 1000;

        // Act
        var solutions = _numbersSolver.FindSolutions(numbers, impossibleTarget);

        // Assert
        solutions.Should().BeEmpty("Should not find solutions for impossible targets");
    }

    [Theory]
    [InlineData(new[] { 25, 50, 75, 100, 3, 6 }, 952)]
    [InlineData(new[] { 2, 3, 4, 5, 6, 7 }, 123)]
    public void FindBestSolution_ShouldReturnOptimalSolution(int[] numbers, int target)
    {
        // Act
        var bestSolution = _numbersSolver.FindBestSolution(numbers, target);

        // Assert
        bestSolution.Should().NotBeNull("Should find a best solution");
        bestSolution.Expression.Should().NotBeNullOrEmpty("Best solution should have an expression");
        bestSolution.Result.Should().BeCloseTo(target, 10, "Best solution should be close to target");
        
        var actualResult = EvaluateExpression(bestSolution.Expression);
        actualResult.Should().Be(bestSolution.Result, "Solution result should match expression evaluation");
    }

    [Fact]
    public void FindBestSolution_ShouldPreferExactMatches()
    {
        // Arrange
        var numbers = new[] { 1, 2, 3, 4, 5, 6 };
        var target = 15; // Can be made exactly with 1+2+3+4+5

        // Act
        var bestSolution = _numbersSolver.FindBestSolution(numbers, target);

        // Assert
        bestSolution.Should().NotBeNull();
        bestSolution.Result.Should().Be(target, "Should find exact match when possible");
    }

    [Theory]
    [InlineData("1 + 2", 3)]
    [InlineData("10 - 5", 5)]
    [InlineData("3 * 4", 12)]
    [InlineData("20 / 4", 5)]
    [InlineData("(1 + 2) * 3", 9)]
    [InlineData("25 + 50 - 3", 72)]
    public void IsValidExpression_ShouldValidateCorrectExpressions(string expression, int expectedResult)
    {
        // Arrange
        var numbers = new[] { 1, 2, 3, 4, 5, 10, 20, 25, 50 };

        // Act
        var isValid = _numbersSolver.IsValidExpression(expression, numbers);

        // Assert
        isValid.Should().BeTrue($"Expression '{expression}' should be valid");
        
        if (isValid)
        {
            var result = EvaluateExpression(expression);
            result.Should().Be(expectedResult, $"Expression '{expression}' should evaluate to {expectedResult}");
        }
    }

    [Theory]
    [InlineData("1 + 7", new[] { 1, 2, 3, 4, 5, 6 })] // 7 not available
    [InlineData("1 + 1 + 1", new[] { 1, 2, 3, 4, 5, 6 })] // Using 1 three times when only one available
    [InlineData("5 / 2", new[] { 2, 5 })] // Non-integer result
    [InlineData("invalid", new[] { 1, 2, 3 })] // Invalid syntax
    public void IsValidExpression_ShouldRejectInvalidExpressions(string expression, int[] availableNumbers)
    {
        // Act
        var isValid = _numbersSolver.IsValidExpression(expression, availableNumbers);

        // Assert
        isValid.Should().BeFalse($"Expression '{expression}' should be invalid");
    }

    [Fact]
    public void FindSolutions_ShouldOnlyUsePositiveIntegers()
    {
        // Arrange
        var numbers = new[] { 1, 2, 3, 4, 5, 6 };
        var target = 7;

        // Act
        var solutions = _numbersSolver.FindSolutions(numbers, target);

        // Assert
        solutions.Should().NotBeEmpty();
        
        foreach (var solution in solutions.Take(10))
        {
            // Verify no negative numbers or non-integers in intermediate steps
            solution.Should().NotContain("-", "Solutions should not use subtraction resulting in negative numbers");
            
            var result = EvaluateExpression(solution);
            result.Should().BeGreaterThan(0, "All intermediate and final results should be positive");
        }
    }

    [Fact]
    public void FindSolutions_ShouldUseEachNumberAtMostOnce()
    {
        // Arrange
        var numbers = new[] { 1, 2, 3, 4, 5, 6 };
        var target = 21; // Sum of all numbers

        // Act
        var solutions = _numbersSolver.FindSolutions(numbers, target);

        // Assert
        solutions.Should().NotBeEmpty();
        
        foreach (var solution in solutions.Take(5))
        {
            VerifyNumberUsage(solution, numbers).Should().BeTrue(
                $"Solution '{solution}' should not use any number more than available");
        }
    }

    [Theory]
    [InlineData(new[] { 25, 50, 75, 100, 1, 2 })]
    [InlineData(new[] { 1, 2, 3, 4, 5, 6 })]
    [InlineData(new[] { 10, 10, 5, 5, 2, 1 })]
    public void Performance_FindSolutions_ShouldCompleteInReasonableTime(int[] numbers)
    {
        // Arrange
        var target = 500;
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        // Act
        var solutions = _numbersSolver.FindSolutions(numbers, target);

        // Assert
        stopwatch.Stop();
        stopwatch.ElapsedMilliseconds.Should().BeLessThan(5000, 
            "Solution finding should complete within 5 seconds");
    }

    [Fact]
    public void GetAllPossibleResults_ShouldReturnValidResults()
    {
        // Arrange
        var numbers = new[] { 1, 2, 3 };

        // Act
        var results = _numbersSolver.GetAllPossibleResults(numbers);

        // Assert
        results.Should().NotBeEmpty();
        results.Should().OnlyContain(r => r > 0, "All results should be positive integers");
        results.Should().OnlyContain(r => r == (int)r, "All results should be integers");
    }

    [Theory]
    [InlineData(new[] { 2, 4 }, 8)] // 2 * 4 = 8
    [InlineData(new[] { 10, 5 }, 2)] // 10 / 5 = 2
    [InlineData(new[] { 3, 7 }, 10)] // 3 + 7 = 10
    [InlineData(new[] { 9, 4 }, 5)] // 9 - 4 = 5
    public void CanMakeTarget_ShouldReturnTrueForPossibleTargets(int[] numbers, int target)
    {
        // Act
        var canMake = _numbersSolver.CanMakeTarget(numbers, target);

        // Assert
        canMake.Should().BeTrue($"Should be able to make {target} from {string.Join(", ", numbers)}");
    }

    [Fact]
    public void GetDifficulty_ShouldReturnReasonableDifficultyScores()
    {
        // Arrange
        var easyNumbers = new[] { 1, 2, 3, 4, 5, 6 };
        var easyTarget = 21; // Sum of all
        
        var hardNumbers = new[] { 25, 50, 75, 100, 7, 8 };
        var hardTarget = 952;

        // Act
        var easyDifficulty = _numbersSolver.GetDifficulty(easyNumbers, easyTarget);
        var hardDifficulty = _numbersSolver.GetDifficulty(hardNumbers, hardTarget);

        // Assert
        easyDifficulty.Should().BeGreaterThan(0, "Easy problems should have positive difficulty");
        hardDifficulty.Should().BeGreaterThan(0, "Hard problems should have positive difficulty");
        hardDifficulty.Should().BeGreaterThan(easyDifficulty, "Hard problems should have higher difficulty");
    }

    private static int EvaluateExpression(string expression)
    {
        // Simple expression evaluator for testing
        // In real implementation, this would be more robust
        try
        {
            var dataTable = new System.Data.DataTable();
            var result = dataTable.Compute(expression, null);
            return Convert.ToInt32(result);
        }
        catch
        {
            return -1; // Invalid expression
        }
    }

    private static bool VerifyNumberUsage(string expression, int[] availableNumbers)
    {
        // Extract numbers from expression and verify usage
        var usedNumbers = new List<int>();
        var tokens = expression.Split(new[] { ' ', '+', '-', '*', '/', '(', ')' }, 
            StringSplitOptions.RemoveEmptyEntries);

        foreach (var token in tokens)
        {
            if (int.TryParse(token, out int number))
            {
                usedNumbers.Add(number);
            }
        }

        // Check that each number is used at most as many times as available
        var availableCounts = availableNumbers.GroupBy(n => n).ToDictionary(g => g.Key, g => g.Count());
        var usedCounts = usedNumbers.GroupBy(n => n).ToDictionary(g => g.Key, g => g.Count());

        foreach (var kvp in usedCounts)
        {
            if (!availableCounts.ContainsKey(kvp.Key) || availableCounts[kvp.Key] < kvp.Value)
            {
                return false;
            }
        }

        return true;
    }
}