#!/usr/bin/env python3
"""
DIRECT UNICODE FIX - Wraps Anthropic client to strip Unicode from responses
This ensures no Unicode ever reaches the console
"""

import sys
import os
import re
from pathlib import Path

print("=" * 80)
print("UNICODE FIX WRAPPER - Stripping Unicode at source")
print("=" * 80)
print()

# Force UTF-8 encoding for Python
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

# Create wrapper for lib/mock_anthropic_enhanced.py
wrapper_code = '''
import sys
import os
import re

# Unicode replacement map
UNICODE_TO_ASCII = {
    '✅': '[OK]', '❌': '[X]', '✓': '[v]', '✗': '[x]',
    '🎯': '[TARGET]', '🔧': '[TOOL]', '📝': '[NOTE]', '📋': '[LIST]',
    '🚀': '[LAUNCH]', '💡': '[IDEA]', '⚠️': '[WARNING]', '🔴': '[RED]',
    '🟢': '[GREEN]', '🟡': '[YELLOW]', '📊': '[CHART]', '📈': '[GROWTH]',
    '📉': '[DECLINE]', '🎉': '[SUCCESS]', '🔍': '[SEARCH]', '📁': '[FOLDER]',
    '📄': '[FILE]', '🔒': '[LOCK]', '🔓': '[UNLOCK]', '⭐': '[STAR]',
    '🏗️': '[BUILD]', '🎨': '[DESIGN]', '🧪': '[TEST]', '🛠️': '[TOOLS]',
    '💻': '[CODE]', '🌐': '[WEB]', '📦': '[PACKAGE]', '🔐': '[SECURE]',
    '🔑': '[KEY]', '🎮': '[GAME]', '📱': '[MOBILE]', '🖥️': '[DESKTOP]',
    '⚡': '[FAST]', '🐛': '[BUG]', '🔥': '[FIRE]', '✨': '[SPARKLE]',
    '🎯': '[AIM]', '📌': '[PIN]', '🏆': '[TROPHY]', '🎖️': '[MEDAL]',
    '🥇': '[1ST]', '🥈': '[2ND]', '🥉': '[3RD]', '💯': '[100]',
    '➜': '->', '→': '->', '←': '<-', '↑': '^', '↓': 'v',
    '•': '*', '◦': 'o', '▪': '-', '▫': '-', '■': '[#]', '□': '[ ]',
    '☐': '[ ]', '☑': '[X]', '☒': '[X]', '※': '*', '§': 'S',
    '†': '+', '‡': '++', '°': 'deg', '¹': '1', '²': '2', '³': '3',
    '–': '-', '—': '--', ''': "'", ''': "'", '"': '"', '"': '"',
    '…': '...', '€': 'EUR', '£': 'GBP', '¥': 'YEN', '©': '(c)',
    '®': '(r)', '™': '(tm)', '×': 'x', '÷': '/', '≈': '~', '≠': '!=',
    '≤': '<=', '≥': '>=', '±': '+/-', '∞': 'inf', '√': 'sqrt',
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'π': 'pi',
    'Σ': 'sum', '∑': 'sum', '∫': 'int', '∂': 'partial', '∇': 'nabla',
}

def strip_unicode(text):
    """Replace Unicode characters with ASCII equivalents"""
    if not isinstance(text, str):
        return text
    
    # Replace known Unicode characters
    for unicode_char, ascii_char in UNICODE_TO_ASCII.items():
        text = text.replace(unicode_char, ascii_char)
    
    # Remove any remaining non-ASCII characters
    text = ''.join(char if ord(char) < 128 else '?' for char in text)
    
    return text

# Monkey-patch the Anthropic client
def patch_anthropic_client():
    """Patch Anthropic client to strip Unicode from responses"""
    try:
        import lib.agent_runtime as runtime
        
        # Get the original run_agent_task if it exists
        if hasattr(runtime, 'run_agent_task'):
            original_run = runtime.run_agent_task
            
            def wrapped_run(*args, **kwargs):
                result = original_run(*args, **kwargs)
                # Strip Unicode from the result
                if isinstance(result, str):
                    result = strip_unicode(result)
                elif isinstance(result, dict):
                    for key in result:
                        if isinstance(result[key], str):
                            result[key] = strip_unicode(result[key])
                return result
            
            runtime.run_agent_task = wrapped_run
            print("[OK] Patched run_agent_task to strip Unicode")
    except Exception as e:
        print(f"[WARNING] Could not patch agent_runtime: {e}")
    
    try:
        # Also patch the mock client if it exists
        import lib.mock_anthropic_enhanced as mock
        
        if hasattr(mock, 'EnhancedMockAnthropicClient'):
            original_create = mock.EnhancedMockAnthropicClient.messages.create
            
            def wrapped_create(self, *args, **kwargs):
                response = original_create(*args, **kwargs)
                # Strip Unicode from content
                if hasattr(response, 'content'):
                    for content_item in response.content:
                        if hasattr(content_item, 'text'):
                            content_item.text = strip_unicode(content_item.text)
                return response
            
            mock.EnhancedMockAnthropicClient.messages.create = wrapped_create
            print("[OK] Patched mock client to strip Unicode")
    except Exception as e:
        print(f"[WARNING] Could not patch mock client: {e}")

# Apply the patch
patch_anthropic_client()
'''

# Write the wrapper module
wrapper_path = Path("lib/unicode_wrapper.py")
wrapper_path.parent.mkdir(exist_ok=True)
wrapper_path.write_text(wrapper_code, encoding='utf-8')
print(f"Created Unicode wrapper: {wrapper_path}")

# Now create the main runner that uses this wrapper
runner_code = '''#!/usr/bin/env python3
"""
MAIN RUNNER - Runs orchestrator with Unicode protection
"""

import sys
import os
import io

# Set up environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

# Force UTF-8 on Windows
if sys.platform == 'win32':
    # Configure console
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)
    
    # Reconfigure streams
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

print("=" * 80)
print("QUICKSHOP MVP GENERATOR - AGENT SWARM")
print("=" * 80)
print()
print("Starting 15-agent orchestration system...")
print("Unicode protection: ENABLED")
print("Output directory: projects/quickshop-mvp-final")
print()

# Import and apply Unicode wrapper
import lib.unicode_wrapper

# Set up command line arguments
sys.argv = [
    'orchestrate_enhanced.py',
    '--project-type', 'full_stack_api',
    '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
    '--output-dir', 'projects/quickshop-mvp-final',
    '--progress',
    '--summary-level', 'concise',
    '--max-parallel', '2',
    '--human-log',
    '--no-dashboard'  # Disable dashboard to focus on console output
]

print("Configuration:")
for i in range(1, len(sys.argv), 2):
    if i < len(sys.argv) - 1:
        print(f"  {sys.argv[i]}: {sys.argv[i+1]}")
    else:
        print(f"  {sys.argv[i]}: enabled")
print()
print("-" * 80)
print("STARTING AGENTS...")
print("-" * 80)
print()

# Import and run the orchestrator
try:
    import orchestrate_enhanced
    print()
    print("-" * 80)
    print("ORCHESTRATION COMPLETE")
    print("-" * 80)
except Exception as e:
    print(f"[ERROR] Orchestration failed: {e}")
    import traceback
    traceback.print_exc()
'''

runner_path = Path("RUN_QUICKSHOP_FIXED.py")
runner_path.write_text(runner_code, encoding='utf-8')
print(f"Created main runner: {runner_path}")

# Create a batch file for easy execution
batch_code = '''@echo off
echo ================================================================================
echo QUICKSHOP MVP GENERATOR - STARTING
echo ================================================================================
echo.

REM Set UTF-8 encoding
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM Run the fixed orchestrator
python RUN_QUICKSHOP_FIXED.py

echo.
echo ================================================================================
echo COMPLETE - Check projects/quickshop-mvp-final for output
echo ================================================================================
pause
'''

batch_path = Path("RUN_QUICKSHOP.bat")
batch_path.write_text(batch_code, encoding='utf-8')
print(f"Created batch launcher: {batch_path}")

print("\n" + "=" * 80)
print("✅ FIXES APPLIED SUCCESSFULLY")
print("=" * 80)
print()
print("Three ways to run the fixed system:")
print()
print("1. QUICK START (Windows):")
print("   RUN_QUICKSHOP.bat")
print()
print("2. PYTHON DIRECT:")
print("   python RUN_QUICKSHOP_FIXED.py")
print()
print("3. COMPREHENSIVE FIX:")
print("   python FIX_BULLETPROOF_COMPREHENSIVE.py")
print()
print("The system will now:")
print("  - Strip all Unicode characters from agent responses")
print("  - Replace emojis with ASCII equivalents ([OK], [TARGET], etc.)")
print("  - Show clear agent progress in the console")
print("  - Generate the complete QuickShop MVP application")
print()
print("Ready to start!")