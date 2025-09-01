using CountdownGame.Shared.Services;
using FluentAssertions;
using Xunit;

namespace CountdownGame.Shared.Tests.Services;

public class DictionaryServiceTests
{
    private readonly DictionaryService _dictionaryService;

    public DictionaryServiceTests()
    {
        _dictionaryService = new DictionaryService();
    }

    [Theory]
    [InlineData("HELLO")]
    [InlineData("WORLD")]
    [InlineData("GAME")]
    [InlineData("TEST")]
    [InlineData("WORD")]
    public void IsValidWord_ShouldReturnTrueForCommonWords(string word)
    {
        // Act
        var isValid = _dictionaryService.IsValidWord(word);

        // Assert
        isValid.Should().BeTrue($"{word} should be a valid dictionary word");
    }

    [Theory]
    [InlineData("ZZZZZ")]
    [InlineData("QWERTY")]
    [InlineData("ASDFGH")]
    [InlineData("NOTAWORD")]
    public void IsValidWord_ShouldReturnFalseForInvalidWords(string word)
    {
        // Act
        var isValid = _dictionaryService.IsValidWord(word);

        // Assert
        isValid.Should().BeFalse($"{word} should not be a valid dictionary word");
    }

    [Theory]
    [InlineData("")]
    [InlineData("A")]
    [InlineData("AB")]
    public void IsValidWord_ShouldReturnFalseForTooShortWords(string word)
    {
        // Act
        var isValid = _dictionaryService.IsValidWord(word);

        // Assert
        isValid.Should().BeFalse($"Words shorter than 3 letters should not be valid: '{word}'");
    }

    [Fact]
    public void IsValidWord_ShouldBeCaseInsensitive()
    {
        // Arrange
        var testWords = new[] { "hello", "HELLO", "Hello", "HeLLo" };

        // Act & Assert
        foreach (var word in testWords)
        {
            var isValid = _dictionaryService.IsValidWord(word);
            isValid.Should().BeTrue($"Dictionary should be case insensitive for: {word}");
        }
    }

    [Fact]
    public void GetBestWords_ShouldReturnWordsInDescendingLengthOrder()
    {
        // Arrange
        var letters = new[] { 'C', 'O', 'U', 'N', 'T', 'D', 'O', 'W', 'N' };

        // Act
        var bestWords = _dictionaryService.GetBestWords(letters, maxResults: 10);

        // Assert
        bestWords.Should().NotBeEmpty();
        
        for (int i = 0; i < bestWords.Count - 1; i++)
        {
            bestWords[i].Length.Should().BeGreaterOrEqualTo(bestWords[i + 1].Length,
                "Words should be ordered by length descending");
        }
    }

    [Fact]
    public void GetBestWords_ShouldOnlyReturnValidWords()
    {
        // Arrange
        var letters = new[] { 'H', 'E', 'L', 'L', 'O', 'W', 'O', 'R', 'L', 'D' };

        // Act
        var bestWords = _dictionaryService.GetBestWords(letters, maxResults: 20);

        // Assert
        bestWords.Should().NotBeEmpty();
        
        foreach (var word in bestWords)
        {
            _dictionaryService.IsValidWord(word).Should().BeTrue($"{word} should be a valid dictionary word");
            CanMakeWordFromLetters(word, letters).Should().BeTrue($"{word} should be makeable from available letters");
        }
    }

    [Fact]
    public void GetBestWords_ShouldRespectMaxResults()
    {
        // Arrange
        var letters = new[] { 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I' };
        var maxResults = 5;

        // Act
        var bestWords = _dictionaryService.GetBestWords(letters, maxResults);

        // Assert
        bestWords.Should().HaveCountLessOrEqualTo(maxResults);
    }

    [Fact]
    public void FindAnagrams_ShouldReturnValidAnagrams()
    {
        // Arrange
        var letters = "LISTEN";

        // Act
        var anagrams = _dictionaryService.FindAnagrams(letters);

        // Assert
        anagrams.Should().NotBeEmpty();
        
        foreach (var anagram in anagrams)
        {
            anagram.Length.Should().Be(letters.Length);
            _dictionaryService.IsValidWord(anagram).Should().BeTrue($"{anagram} should be a valid word");
            
            // Check that anagram uses exactly the same letters
            var sortedOriginal = string.Concat(letters.OrderBy(c => c));
            var sortedAnagram = string.Concat(anagram.ToUpper().OrderBy(c => c));
            sortedAnagram.Should().Be(sortedOriginal, $"{anagram} should be an anagram of {letters}");
        }
    }

    [Theory]
    [InlineData("LISTEN", "SILENT")]
    [InlineData("EARTH", "HEART")]
    [InlineData("DEAR", "READ")]
    public void AreAnagrams_ShouldReturnTrueForValidAnagrams(string word1, string word2)
    {
        // Act
        var areAnagrams = _dictionaryService.AreAnagrams(word1, word2);

        // Assert
        areAnagrams.Should().BeTrue($"{word1} and {word2} should be anagrams");
    }

    [Theory]
    [InlineData("HELLO", "WORLD")]
    [InlineData("CAT", "DOG")]
    [InlineData("TEST", "BEST")]
    public void AreAnagrams_ShouldReturnFalseForNonAnagrams(string word1, string word2)
    {
        // Act
        var areAnagrams = _dictionaryService.AreAnagrams(word1, word2);

        // Assert
        areAnagrams.Should().BeFalse($"{word1} and {word2} should not be anagrams");
    }

    [Fact]
    public void GetWordFrequency_ShouldReturnReasonableValues()
    {
        // Arrange
        var commonWord = "THE";
        var uncommonWord = "ZYGOTE";

        // Act
        var commonFreq = _dictionaryService.GetWordFrequency(commonWord);
        var uncommonFreq = _dictionaryService.GetWordFrequency(uncommonWord);

        // Assert
        commonFreq.Should().BeGreaterThan(0);
        uncommonFreq.Should().BeGreaterOrEqualTo(0);
        
        if (uncommonFreq > 0)
        {
            commonFreq.Should().BeGreaterThan(uncommonFreq, 
                "Common words should have higher frequency than uncommon words");
        }
    }

    [Fact]
    public void LoadDictionary_ShouldLoadSuccessfully()
    {
        // Act
        var loadResult = _dictionaryService.LoadDictionary();

        // Assert
        loadResult.Should().BeTrue("Dictionary should load successfully");
        
        // Verify dictionary is functional after loading
        _dictionaryService.IsValidWord("TEST").Should().BeTrue("Dictionary should work after loading");
    }

    [Fact]
    public void GetDictionaryStats_ShouldReturnValidStats()
    {
        // Act
        var stats = _dictionaryService.GetDictionaryStats();

        // Assert
        stats.Should().NotBeNull();
        stats.TotalWords.Should().BeGreaterThan(0, "Dictionary should contain words");
        stats.MinWordLength.Should().BeGreaterOrEqualTo(3, "Minimum word length should be at least 3");
        stats.MaxWordLength.Should().BeLessOrEqualTo(20, "Maximum word length should be reasonable");
        stats.MinWordLength.Should().BeLessOrEqualTo(stats.MaxWordLength);
    }

    [Theory]
    [InlineData(3)]
    [InlineData(4)]
    [InlineData(5)]
    [InlineData(6)]
    [InlineData(7)]
    [InlineData(8)]
    [InlineData(9)]
    public void GetWordsByLength_ShouldReturnWordsOfCorrectLength(int length)
    {
        // Act
        var words = _dictionaryService.GetWordsByLength(length);

        // Assert
        words.Should().NotBeEmpty($"Should have words of length {length}");
        words.Should().OnlyContain(w => w.Length == length, $"All words should be exactly {length} characters long");
    }

    [Fact]
    public void Performance_IsValidWord_ShouldBeReasonablyFast()
    {
        // Arrange
        var testWords = new[] { "HELLO", "WORLD", "GAME", "TEST", "PERFORMANCE" };
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        // Act
        for (int i = 0; i < 1000; i++)
        {
            foreach (var word in testWords)
            {
                _dictionaryService.IsValidWord(word);
            }
        }

        // Assert
        stopwatch.Stop();
        var wordsPerSecond = (1000 * testWords.Length) / stopwatch.Elapsed.TotalSeconds;
        wordsPerSecond.Should().BeGreaterThan(10000, 
            "Dictionary should validate at least 10,000 words per second as per requirements");
    }

    private static bool CanMakeWordFromLetters(string word, char[] availableLetters)
    {
        var letterCounts = availableLetters.GroupBy(c => char.ToUpper(c))
            .ToDictionary(g => g.Key, g => g.Count());

        foreach (var letter in word.ToUpper())
        {
            if (!letterCounts.ContainsKey(letter) || letterCounts[letter] == 0)
            {
                return false;
            }
            letterCounts[letter]--;
        }

        return true;
    }
}