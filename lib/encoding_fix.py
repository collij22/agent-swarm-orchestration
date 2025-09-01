"""
Comprehensive encoding fixes for Windows compatibility
This module ensures UTF-8 encoding is used throughout the system
"""

import sys
import os
import io
import codecs
import locale
import re

def setup_utf8_encoding():
    """Set up UTF-8 encoding for the entire Python environment"""
    
    # 1. Set environment variables for UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    # 2. Reconfigure stdout and stderr to use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        # For older Python versions, replace stdout
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace',
            line_buffering=True
        )
    
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
    
    # 3. Set stdin encoding
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    
    # 4. Set default encoding for open() function
    if hasattr(locale, 'getpreferredencoding'):
        # Override the default encoding
        def get_utf8_encoding(do_setlocale=True):
            return 'utf-8'
        locale.getpreferredencoding = get_utf8_encoding
    
    # 5. Set codecs default encoding
    if sys.platform == 'win32':
        # Force UTF-8 for file operations on Windows
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'mbcs' else None)
    
    return True

def clean_unicode_content(content: str) -> str:
    """
    Clean Unicode characters from content for Windows compatibility
    More comprehensive than the logger version
    """
    if not content:
        return content
    
    # Common Unicode to ASCII replacements
    replacements = {
        # Checkmarks and crosses
        '✅': '[OK]',
        '✓': '[OK]',
        '✔': '[OK]',
        '☑': '[OK]',
        '✗': '[X]',
        '✘': '[X]',
        '❌': '[X]',
        '❎': '[X]',
        
        # Arrows
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '↔': '<->',
        '⇒': '=>',
        '⇐': '<=',
        '⇔': '<=>',
        
        # Progress indicators
        '⚠️': '[WARNING]',
        '⚡': '[FAST]',
        '🔥': '[HOT]',
        '🚀': '[LAUNCH]',
        '💡': '[IDEA]',
        '🎯': '[TARGET]',
        '📝': '[NOTE]',
        '📊': '[CHART]',
        '🔧': '[TOOL]',
        '🛠️': '[TOOLS]',
        '⚙️': '[SETTINGS]',
        '🔍': '[SEARCH]',
        '📁': '[FOLDER]',
        '📄': '[FILE]',
        '💻': '[CODE]',
        '🐛': '[BUG]',
        '🎨': '[DESIGN]',
        '✨': '[NEW]',
        '🔒': '[LOCKED]',
        '🔓': '[UNLOCKED]',
        '🎉': '[CELEBRATE]',
        '⏰': '[TIME]',
        '📈': '[GROWTH]',
        '📉': '[DECLINE]',
        '✉️': '[EMAIL]',
        '📧': '[EMAIL]',
        
        # Special characters
        '•': '*',
        '◦': 'o',
        '▪': '-',
        '▫': '-',
        '■': '[#]',
        '□': '[ ]',
        '▲': '^',
        '▼': 'v',
        '◆': '<>',
        '○': 'o',
        '●': '*',
        '★': '*',
        '☆': 'o',
        '©': '(c)',
        '®': '(R)',
        '™': '(TM)',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
        '°': 'deg',
        '±': '+/-',
        '×': 'x',
        '÷': '/',
        '≈': '~',
        '≠': '!=',
        '≤': '<=',
        '≥': '>=',
        '∞': 'inf',
        '√': 'sqrt',
        '∑': 'sum',
        '∏': 'prod',
        '∈': 'in',
        '∉': 'not in',
        '∪': 'union',
        '∩': 'intersect',
        '⊂': 'subset',
        '⊃': 'superset',
        '∅': 'empty',
        '∀': 'for all',
        '∃': 'exists',
        '∴': 'therefore',
        '∵': 'because',
    }
    
    # Apply replacements
    for unicode_char, ascii_replacement in replacements.items():
        content = content.replace(unicode_char, ascii_replacement)
    
    # Remove any remaining non-ASCII characters that might cause issues
    # This is more lenient than the aggressive removal in the logger
    content = re.sub(r'[\u2000-\u206F]', ' ', content)  # General punctuation
    content = re.sub(r'[\u2070-\u209F]', '', content)   # Superscripts/subscripts
    content = re.sub(r'[\u20A0-\u20CF]', '', content)   # Currency symbols
    content = re.sub(r'[\u2100-\u214F]', '', content)   # Letterlike symbols
    content = re.sub(r'[\u2200-\u22FF]', '', content)   # Mathematical operators
    content = re.sub(r'[\u2300-\u23FF]', '', content)   # Miscellaneous technical
    content = re.sub(r'[\u2400-\u243F]', '', content)   # Control pictures
    content = re.sub(r'[\u2440-\u245F]', '', content)   # OCR
    content = re.sub(r'[\u2460-\u24FF]', '', content)   # Enclosed alphanumerics
    content = re.sub(r'[\u2500-\u257F]', '-', content)  # Box drawing -> simple lines
    content = re.sub(r'[\u2580-\u259F]', '#', content)  # Block elements
    content = re.sub(r'[\u25A0-\u25FF]', '*', content)  # Geometric shapes
    content = re.sub(r'[\u2600-\u26FF]', '*', content)  # Miscellaneous symbols
    content = re.sub(r'[\u2700-\u27BF]', '*', content)  # Dingbats
    
    # Remove emoji ranges
    content = re.sub(r'[\U0001F000-\U0001F9FF]', '', content)  # Various emoji
    content = re.sub(r'[\U0001FA00-\U0001FAFF]', '', content)  # More emoji
    
    return content

def safe_file_write(filepath: str, content: str, encoding: str = 'utf-8'):
    """
    Safely write content to a file with proper encoding handling
    """
    import pathlib
    
    path = pathlib.Path(filepath)
    
    # Clean the content first
    content = clean_unicode_content(content)
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to write with UTF-8 first
    try:
        path.write_text(content, encoding='utf-8')
    except UnicodeEncodeError:
        # Fallback to ASCII with replacement
        try:
            content_ascii = content.encode('ascii', 'replace').decode('ascii')
            path.write_text(content_ascii, encoding='utf-8')
        except Exception as e:
            # Last resort: write as binary
            content_bytes = content.encode('utf-8', 'replace')
            path.write_bytes(content_bytes)
            print(f"Warning: Had to write {filepath} as binary due to encoding issues: {e}")

def safe_file_read(filepath: str, encoding: str = 'utf-8') -> str:
    """
    Safely read content from a file with proper encoding handling
    """
    import pathlib
    
    path = pathlib.Path(filepath)
    
    if not path.exists():
        return ""
    
    # Try UTF-8 first
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Try with error replacement
        try:
            return path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            # Try different encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return path.read_text(encoding=enc)
                except Exception:
                    continue
            
            # Last resort: read as binary and decode with replacement
            try:
                content_bytes = path.read_bytes()
                return content_bytes.decode('utf-8', 'replace')
            except Exception as e:
                print(f"Warning: Could not read {filepath} properly: {e}")
                return ""

# Automatically set up UTF-8 when this module is imported
setup_utf8_encoding()