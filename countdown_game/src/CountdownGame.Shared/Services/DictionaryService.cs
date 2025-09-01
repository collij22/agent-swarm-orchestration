using Microsoft.Extensions.Logging;

namespace CountdownGame.Shared.Services;

public class DictionaryService
{
    private readonly ILogger<DictionaryService>? _logger;
    private readonly HashSet<string> _dictionary;

    public DictionaryService() : this(null!)
    {
    }

    public DictionaryService(ILogger<DictionaryService>? logger)
    {
        _logger = logger;
        _dictionary = InitializeDictionary();
    }

    // Synchronous version (for tests and sync contexts)
    public bool IsValidWord(string word)
    {
        if (string.IsNullOrWhiteSpace(word) || word.Length < 3)
            return false;

        var normalizedWord = word.ToUpper().Trim();
        return _dictionary.Contains(normalizedWord);
    }

    // Async version (for production use)
    public async Task<bool> IsValidWordAsync(string word)
    {
        if (string.IsNullOrWhiteSpace(word))
            return false;

        var normalizedWord = word.ToUpper().Trim();
        
        // Simulate async dictionary lookup
        await Task.Delay(1); 
        
        return _dictionary.Contains(normalizedWord);
    }

    public async Task<List<string>> FindAllWords(List<char> letters, int minLength = 3)
    {
        var words = new List<string>();
        var letterCounts = letters.GroupBy(c => c).ToDictionary(g => g.Key, g => g.Count());

        await Task.Run(() =>
        {
            foreach (var word in _dictionary.Where(w => w.Length >= minLength))
            {
                if (CanMakeWord(word, letterCounts))
                {
                    words.Add(word);
                }
            }
        });

        return words.OrderByDescending(w => w.Length).ThenBy(w => w).ToList();
    }

    private bool CanMakeWord(string word, Dictionary<char, int> availableLetters)
    {
        var wordLetters = word.GroupBy(c => c).ToDictionary(g => g.Key, g => g.Count());
        
        foreach (var kvp in wordLetters)
        {
            if (!availableLetters.ContainsKey(kvp.Key) || availableLetters[kvp.Key] < kvp.Value)
            {
                return false;
            }
        }
        
        return true;
    }

    private HashSet<string> InitializeDictionary()
    {
        // Simplified dictionary - in real implementation would load from file/database
        var words = new HashSet<string>
        {
            // Common 3-letter words
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", "WAS", "ONE", "OUR",
            "HAD", "BUT", "WOR", "BOY", "DID", "ITS", "LET", "PUT", "SAY", "SHE", "TOO", "USE", "DAY",
            "GET", "HAS", "HIM", "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE", "TWO", "WAY",
            "WHO", "BOY", "DID", "ITS", "LET", "MAN", "NEW", "NOW", "OLD", "PUT", "RUN", "SAY", "SHE",
            "TOO", "USE", "WAS", "WIN", "YES", "YET", "YOU", "BAD", "BAG", "BED", "BIG", "BOX", "BUS",
            "CAR", "CAT", "COW", "CRY", "CUP", "CUT", "DOG", "EAR", "EAT", "EGG", "END", "EYE", "FAR",
            "FLY", "FUN", "GOT", "GUN", "HAT", "HIT", "HOT", "JOB", "LEG", "LIE", "LOT", "LOW", "MAP",
            "MOM", "PEN", "PET", "PIG", "RED", "RUN", "SAD", "SIT", "SIX", "SUN", "TEN", "TOP", "TRY",
            
            // Common 4-letter words
            "THAT", "WITH", "HAVE", "THIS", "WILL", "YOUR", "FROM", "THEY", "KNOW", "WANT", "BEEN",
            "GOOD", "MUCH", "SOME", "TIME", "VERY", "WHEN", "COME", "HERE", "JUST", "LIKE", "LONG",
            "MAKE", "MANY", "OVER", "SUCH", "TAKE", "THAN", "THEM", "WELL", "WERE", "WHAT", "WHERE",
            "WORK", "YEAR", "BACK", "CALL", "CAME", "EACH", "EVEN", "FIND", "GIVE", "HAND", "HIGH",
            "KEEP", "LAST", "LEFT", "LIFE", "LIVE", "LOOK", "MADE", "MOST", "MOVE", "MUST", "NAME",
            "NEED", "NEXT", "ONLY", "OPEN", "PART", "PLAY", "RIGHT", "SAID", "SAME", "SEEM", "SHOW",
            "SIDE", "TELL", "TURN", "USED", "WANT", "WAYS", "WEEK", "WENT", "WORD", "WORK", "YEAR",
            
            // Common 5-letter words
            "ABOUT", "AFTER", "AGAIN", "COULD", "EVERY", "FIRST", "FOUND", "GREAT", "GROUP", "HOUSE",
            "LARGE", "NEVER", "OTHER", "PLACE", "RIGHT", "SMALL", "SOUND", "STILL", "THEIR", "THERE",
            "THESE", "THING", "THINK", "THREE", "WATER", "WORLD", "WOULD", "WRITE", "YOUNG", "ASKED",
            "BEING", "BELOW", "BUILD", "CARRY", "CLEAN", "CLOSE", "DOING", "EARLY", "EARTH", "FIELD",
            "FINAL", "FORCE", "FRONT", "GIVEN", "GOING", "GREEN", "HEARD", "HEART", "HEAVY", "HORSE",
            "LIGHT", "LIVED", "LOCAL", "MIGHT", "MONEY", "MUSIC", "NORTH", "OFTEN", "ORDER", "PAPER",
            "PARTY", "PEACE", "POINT", "POWER", "QUICK", "QUITE", "REACH", "RIVER", "ROUND", "SERVE",
            "SHALL", "SHORT", "SINCE", "SOUTH", "SPACE", "SPEAK", "SPEED", "SPEND", "STOOD", "STORY",
            "STUDY", "TAKEN", "TODAY", "TOUCH", "TRADE", "TRIED", "TRULY", "UNDER", "UNTIL", "USING",
            "VALUE", "VOICE", "WATCH", "WEEKS", "WHEEL", "WHILE", "WHITE", "WHOLE", "WHOSE", "WOMAN",
            
            // Common 6+ letter words
            "AROUND", "BEFORE", "BETTER", "CHANGE", "CHURCH", "COMING", "COURSE", "DURING", "ENOUGH",
            "FAMILY", "FATHER", "FOLLOW", "FRIEND", "GROUND", "HAVING", "INSIDE", "LETTER", "LISTEN",
            "LIVING", "MAKING", "MATTER", "MINUTE", "MOMENT", "MOTHER", "MOVING", "NATION", "NATURE",
            "NEARLY", "NEEDED", "NUMBER", "OFFICE", "OPENED", "PEOPLE", "PERSON", "PUBLIC", "RATHER",
            "REALLY", "REASON", "RECORD", "RESULT", "SCHOOL", "SECOND", "SHOULD", "SIMPLE", "SINGLE",
            "SOCIAL", "SYSTEM", "TAKING", "TRYING", "TURNED", "WANTED", "WINDOW", "WITHIN", "WONDER",
            "WORKING", "WRITING", "ALREADY", "ANOTHER", "BETWEEN", "COMPANY", "COUNTRY", "DEVELOP",
            "EXAMPLE", "GENERAL", "GETTING", "HOWEVER", "INCLUDE", "LOOKING", "NOTHING", "PROBLEM",
            "PROGRAM", "PROVIDE", "RUNNING", "SERVICE", "SEVERAL", "SPECIAL", "SUPPORT", "THROUGH",
            "TOGETHER", "VARIOUS", "WITHOUT", "BUSINESS", "CHILDREN", "COMPLETE", "CONSIDER",
            "CONTINUE", "DECISION", "DESCRIBE", "DISCOVER", "DISTRICT", "EDUCATION", "ESTABLISH",
            "EVIDENCE", "EXCHANGE", "EXERCISE", "EXPERIENCE", "GOVERNMENT", "IMPORTANT", "INCREASE",
            "INTEREST", "LANGUAGE", "MATERIAL", "NATIONAL", "ORIGINAL", "PERSONAL", "POLITICAL",
            "POSSIBLE", "PRACTICE", "PRESSURE", "PROBABLY", "QUESTION", "RESEARCH", "RESOURCE",
            "RESPONSE", "SECURITY", "SEPARATE", "STANDARD", "STRENGTH", "STRUCTURE", "TOGETHER",
            "TREATMENT", "UNDERSTAND", "UNIVERSITY"
        };

        _logger?.LogInformation("Loaded dictionary with {WordCount} words", words.Count);
        return words;
    }


    public List<string> GetBestWords(char[] letters, int maxResults = 10)
    {
        var letterCounts = letters.GroupBy(c => char.ToUpper(c))
            .ToDictionary(g => g.Key, g => g.Count());

        var validWords = new List<string>();
        foreach (var word in _dictionary)
        {
            if (CanMakeWord(word, letterCounts))
            {
                validWords.Add(word);
            }
        }

        return validWords
            .OrderByDescending(w => w.Length)
            .ThenBy(w => w)
            .Take(maxResults)
            .ToList();
    }

    public List<string> FindAnagrams(string letters)
    {
        var normalizedLetters = letters.ToUpper();
        var lettersSorted = string.Concat(normalizedLetters.OrderBy(c => c));
        var anagrams = new List<string>();

        foreach (var word in _dictionary.Where(w => w.Length == letters.Length))
        {
            var wordSorted = string.Concat(word.OrderBy(c => c));
            if (wordSorted == lettersSorted)
            {
                anagrams.Add(word);
            }
        }

        return anagrams;
    }

    public bool AreAnagrams(string word1, string word2)
    {
        if (word1.Length != word2.Length)
            return false;

        var sorted1 = string.Concat(word1.ToUpper().OrderBy(c => c));
        var sorted2 = string.Concat(word2.ToUpper().OrderBy(c => c));
        return sorted1 == sorted2;
    }

    public double GetWordFrequency(string word)
    {
        // Simple frequency based on word commonality
        var commonWords = new[] { "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL" };
        if (commonWords.Contains(word.ToUpper()))
            return 100.0;
        
        return _dictionary.Contains(word.ToUpper()) ? 50.0 : 0.0;
    }

    public bool LoadDictionary()
    {
        // Dictionary is loaded in constructor
        return _dictionary.Count > 0;
    }


    public DictionaryStats GetDictionaryStats()
    {
        return new DictionaryStats
        {
            TotalWords = _dictionary.Count,
            MinWordLength = _dictionary.Min(w => w.Length),
            MaxWordLength = _dictionary.Max(w => w.Length)
        };
    }

    public List<string> GetWordsByLength(int length)
    {
        return _dictionary.Where(w => w.Length == length).ToList();
    }
}

public class DictionaryStats
{
    public int TotalWords { get; set; }
    public int MinWordLength { get; set; }
    public int MaxWordLength { get; set; }
}