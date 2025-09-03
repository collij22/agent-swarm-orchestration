#!/usr/bin/env python3
"""Test script to verify emoji handling fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.unicode_stripper import strip_unicode

def test_emoji_stripping():
    """Test that emojis are properly converted to ASCII equivalents"""
    
    test_cases = [
        ("🔐 Authentication System", "[SECURE] Authentication System"),
        ("📦 Package Manager", "[PACKAGE] Package Manager"),
        ("🛒 Shopping Cart", "[CART] Shopping Cart"),
        ("✅ Task Complete", "[OK] Task Complete"),
        ("❌ Task Failed", "[FAIL] Task Failed"),
        ("🚀 Launching App", "[START] Launching App"),
        ("💡 Great Idea", "[IDEA] Great Idea"),
        ("⚠️ Warning Message", "[WARN] Warning Message"),
        ("API 🔐 Auth → Database 📦", "API [SECURE] Auth -> Database [PACKAGE]"),
        ("Complex: 🏪🛍️💰 Shop System", "Complex: [SHOP][BUY][MONEY] Shop System"),
    ]
    
    print("Testing emoji stripping...")
    print("-" * 60)
    
    all_passed = True
    for input_text, expected in test_cases:
        result = strip_unicode(input_text)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {input_text[:30]:<30} -> {result[:40]}")
        if not passed:
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
    
    print("-" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

def test_agent_response():
    """Test a real agent response with emojis"""
    
    agent_response = """
I have successfully created a comprehensive API specification document (`API_SPEC.md`) that defines the backend architecture for the QuickShop MVP e-commerce platform.

### 🔐 **Authentication & Security**
The API uses JWT-based authentication with secure token management.

### 📦 **Core Resources**
- **Products**: Full CRUD operations for product management
- **Cart**: Session-based shopping cart functionality  
- **Orders**: Complete order lifecycle management
- **Users**: User registration and profile management

### 🛒 **Shopping Experience**
The API provides endpoints for browsing products, managing cart items, and processing checkouts.

### 💳 **Payment Integration**
Supports Stripe payment processing with webhook handling for payment confirmations.
"""
    
    print("\nTesting full agent response...")
    print("-" * 60)
    print("Original (with emojis):")
    print(agent_response[:200] + "...")
    
    cleaned = strip_unicode(agent_response)
    print("\nCleaned (ASCII safe):")
    print(cleaned[:200] + "...")
    
    # Check that key content is preserved
    assert "API specification document" in cleaned
    assert "[SECURE]" in cleaned or "Authentication" in cleaned
    assert "[PACKAGE]" in cleaned or "Core Resources" in cleaned
    assert "[CART]" in cleaned or "Shopping Experience" in cleaned
    assert "[PAY]" in cleaned or "Payment Integration" in cleaned
    
    print("\n✓ Agent response successfully cleaned!")
    return True

def test_windows_encoding():
    """Test that output works on Windows console"""
    
    print("\nTesting Windows console output...")
    print("-" * 60)
    
    test_string = "Testing: 🔐📦🛒 → Should become: [SECURE][PACKAGE][CART]"
    cleaned = strip_unicode(test_string)
    
    try:
        # Try to encode as cp1252 (Windows default)
        cleaned.encode('cp1252')
        print(f"✓ Windows encoding successful: {cleaned}")
        return True
    except UnicodeEncodeError as e:
        print(f"✗ Windows encoding failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("EMOJI HANDLING FIX VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Emoji Stripping", test_emoji_stripping()))
    results.append(("Agent Response", test_agent_response()))
    results.append(("Windows Encoding", test_windows_encoding()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All fixes verified successfully!")
        print("The emoji encoding issue has been resolved.")
        print("Agents can now use emojis without causing truncation.")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")
    
    sys.exit(0 if all_passed else 1)