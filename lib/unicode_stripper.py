
"""Unicode stripper module - removes/replaces Unicode characters"""

import re

UNICODE_MAP = {
    # Checkmarks and crosses
    '✅': '[OK]', '❌': '[FAIL]', '✓': '[YES]', '✗': '[NO]', '☑': '[X]',
    
    # Symbols and icons
    '🎯': '[TARGET]', '🔧': '[TOOL]', '📝': '[NOTE]', '📋': '[LIST]',
    '🚀': '[START]', '💡': '[IDEA]', '⚠️': '[WARN]', '🔴': '[ERROR]',
    '🟢': '[OK]', '🟡': '[WAIT]', '📊': '[DATA]', '📈': '[UP]',
    '📉': '[DOWN]', '🎉': '[DONE]', '🔍': '[SEARCH]', '📁': '[FOLDER]',
    '📄': '[FILE]', '🔒': '[LOCK]', '🔓': '[UNLOCK]', '⭐': '[STAR]',
    '🏗️': '[BUILD]', '🎨': '[DESIGN]', '🧪': '[TEST]', '🛠️': '[FIX]',
    '💻': '[CODE]', '🌐': '[WEB]', '📦': '[PACKAGE]', '🔐': '[SECURE]',
    '🛒': '[CART]', '💳': '[PAY]', '📧': '[EMAIL]', '🔑': '[KEY]',
    '⚙️': '[CONFIG]', '📡': '[API]', '🗄️': '[DB]', '🎭': '[UI]',
    '🏪': '[SHOP]', '🛍️': '[BUY]', '💰': '[MONEY]', '📮': '[SEND]',
    
    # Arrows and bullets
    '→': '->', '←': '<-', '↑': '^', '↓': 'v', '➜': '=>',
    '•': '*', '◦': 'o', '▪': '-', '■': '#', '□': '[ ]',
    
    # Special characters
    '—': '--', '–': '-', '…': '...', ''': "'", ''': "'",
    '"': '"', '"': '"', '©': '(c)', '®': '(R)', '™': '(TM)', 
    '°': 'deg', '±': '+/-', '×': 'x', '÷': '/',
}

def strip_unicode(text):
    """Remove or replace Unicode characters - safe for Windows console"""
    if not isinstance(text, str):
        return text
    
    # First, replace known Unicode characters
    for old, new in UNICODE_MAP.items():
        text = text.replace(old, new)
    
    # Remove any remaining emoji using regex
    # This pattern covers most emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\U0001FA70-\U0001FAFF"  # extended symbols
        "]+", 
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Finally, ensure only ASCII characters remain
    # Use 'replace' to avoid losing too much content
    text = text.encode('ascii', 'replace').decode('ascii')
    # Clean up the replacement character (?)
    text = text.replace('?', '')
    
    return text

def patch_print():
    """Patch the print function to strip Unicode"""
    import builtins
    original_print = builtins.print
    
    def safe_print(*args, **kwargs):
        new_args = []
        for arg in args:
            if isinstance(arg, str):
                arg = strip_unicode(arg)
            new_args.append(arg)
        return original_print(*new_args, **kwargs)
    
    builtins.print = safe_print

# Apply the patch
patch_print()
