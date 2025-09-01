using Microsoft.Extensions.Logging;
using System.Text.RegularExpressions;

namespace CountdownGame.Shared.Services;

public class NumbersSolver
{
    private readonly ILogger<NumbersSolver>? _logger;

    public NumbersSolver() : this(null!)
    {
    }

    public NumbersSolver(ILogger<NumbersSolver>? logger)
    {
        _logger = logger;
    }

    public int EvaluateExpression(string expression, List<int> availableNumbers)
    {
        if (string.IsNullOrWhiteSpace(expression))
            throw new ArgumentException("Expression cannot be empty");

        // Validate expression format
        if (!IsValidExpression(expression))
            throw new ArgumentException("Invalid expression format");

        // Extract numbers from expression
        var usedNumbers = ExtractNumbers(expression);
        
        // Validate that only available numbers are used
        ValidateNumberUsage(usedNumbers, availableNumbers);

        // Evaluate the expression
        var result = EvaluateMathExpression(expression);
        
        if (result < 0)
            throw new ArgumentException("Result cannot be negative");

        return result;
    }

    public List<string> FindSolutions(List<int> numbers, int target, int maxSolutions = 10)
    {
        var solutions = new List<string>();
        var operations = new[] { "+", "-", "*", "/" };
        
        // Generate all possible combinations and permutations
        // This is a simplified version - full implementation would be more comprehensive
        
        for (int i = 0; i < numbers.Count && solutions.Count < maxSolutions; i++)
        {
            for (int j = 0; j < numbers.Count && solutions.Count < maxSolutions; j++)
            {
                if (i == j) continue;
                
                foreach (var op in operations)
                {
                    if (solutions.Count >= maxSolutions) break;
                    
                    var expr = $"{numbers[i]} {op} {numbers[j]}";
                    try
                    {
                        var result = EvaluateMathExpression(expr);
                        if (result == target)
                        {
                            solutions.Add(expr);
                        }
                    }
                    catch
                    {
                        // Invalid expression, continue
                    }
                }
            }
        }

        // Try more complex expressions with 3 numbers
        for (int i = 0; i < numbers.Count && solutions.Count < maxSolutions; i++)
        {
            for (int j = 0; j < numbers.Count && solutions.Count < maxSolutions; j++)
            {
                for (int k = 0; k < numbers.Count && solutions.Count < maxSolutions; k++)
                {
                    if (i == j || j == k || i == k) continue;
                    
                    foreach (var op1 in operations)
                    {
                        foreach (var op2 in operations)
                        {
                            if (solutions.Count >= maxSolutions) break;
                            
                            var expr = $"({numbers[i]} {op1} {numbers[j]}) {op2} {numbers[k]}";
                            try
                            {
                                var result = EvaluateMathExpression(expr);
                                if (result == target)
                                {
                                    solutions.Add(expr);
                                }
                            }
                            catch
                            {
                                // Invalid expression, continue
                            }
                        }
                    }
                }
            }
        }

        return solutions.Distinct().ToList();
    }

    private bool IsValidExpression(string expression)
    {
        // Check for valid characters (numbers, operators, parentheses, spaces)
        var validPattern = @"^[\d\+\-\*\/\(\)\s]+$";
        if (!Regex.IsMatch(expression, validPattern))
            return false;

        // Check for balanced parentheses
        int openParens = 0;
        foreach (char c in expression)
        {
            if (c == '(') openParens++;
            else if (c == ')') openParens--;
            if (openParens < 0) return false;
        }
        
        return openParens == 0;
    }

    private List<int> ExtractNumbers(string expression)
    {
        var numbers = new List<int>();
        var matches = Regex.Matches(expression, @"\d+");
        
        foreach (Match match in matches)
        {
            if (int.TryParse(match.Value, out int number))
            {
                numbers.Add(number);
            }
        }
        
        return numbers;
    }

    private void ValidateNumberUsage(List<int> usedNumbers, List<int> availableNumbers)
    {
        var availableCounts = availableNumbers.GroupBy(n => n).ToDictionary(g => g.Key, g => g.Count());
        var usedCounts = usedNumbers.GroupBy(n => n).ToDictionary(g => g.Key, g => g.Count());

        foreach (var kvp in usedCounts)
        {
            if (!availableCounts.ContainsKey(kvp.Key) || availableCounts[kvp.Key] < kvp.Value)
            {
                throw new ArgumentException($"Number {kvp.Key} used more times than available");
            }
        }
    }

    private int EvaluateMathExpression(string expression)
    {
        try
        {
            // Simple recursive descent parser for basic arithmetic
            var tokens = Tokenize(expression);
            var index = 0;
            var result = ParseExpression(tokens, ref index);
            
            if (index != tokens.Count)
                throw new ArgumentException("Invalid expression");
                
            return result;
        }
        catch (Exception ex)
        {
            _logger?.LogWarning("Failed to evaluate expression '{Expression}': {Error}", expression, ex.Message);
            throw new ArgumentException($"Invalid expression: {ex.Message}");
        }
    }

    private List<string> Tokenize(string expression)
    {
        var tokens = new List<string>();
        var current = "";
        
        foreach (char c in expression.Replace(" ", ""))
        {
            if (char.IsDigit(c))
            {
                current += c;
            }
            else
            {
                if (!string.IsNullOrEmpty(current))
                {
                    tokens.Add(current);
                    current = "";
                }
                tokens.Add(c.ToString());
            }
        }
        
        if (!string.IsNullOrEmpty(current))
        {
            tokens.Add(current);
        }
        
        return tokens;
    }

    private int ParseExpression(List<string> tokens, ref int index)
    {
        var left = ParseTerm(tokens, ref index);
        
        while (index < tokens.Count && (tokens[index] == "+" || tokens[index] == "-"))
        {
            var op = tokens[index++];
            var right = ParseTerm(tokens, ref index);
            
            if (op == "+")
                left += right;
            else
                left -= right;
        }
        
        return left;
    }

    private int ParseTerm(List<string> tokens, ref int index)
    {
        var left = ParseFactor(tokens, ref index);
        
        while (index < tokens.Count && (tokens[index] == "*" || tokens[index] == "/"))
        {
            var op = tokens[index++];
            var right = ParseFactor(tokens, ref index);
            
            if (op == "*")
                left *= right;
            else
            {
                if (right == 0)
                    throw new DivideByZeroException("Division by zero");
                if (left % right != 0)
                    throw new ArgumentException("Division must result in whole number");
                left /= right;
            }
        }
        
        return left;
    }

    private int ParseFactor(List<string> tokens, ref int index)
    {
        if (index >= tokens.Count)
            throw new ArgumentException("Unexpected end of expression");
            
        if (tokens[index] == "(")
        {
            index++; // skip '('
            var result = ParseExpression(tokens, ref index);
            if (index >= tokens.Count || tokens[index] != ")")
                throw new ArgumentException("Missing closing parenthesis");
            index++; // skip ')'
            return result;
        }
        
        if (int.TryParse(tokens[index], out int number))
        {
            index++;
            return number;
        }
        
        throw new ArgumentException($"Invalid token: {tokens[index]}");
    }
}