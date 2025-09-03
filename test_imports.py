import sys
print("1. Starting imports...")

try:
    from rich.console import Console
    print("2. Rich imported OK")
    console = Console()
    print("3. Console created OK")
    console.print("4. Console print works!")
except Exception as e:
    print(f"Rich error: {e}")

try:
    import asyncio
    print("5. asyncio imported OK")
    
    async def test():
        print("6. Inside async function")
        return True
    
    result = asyncio.run(test())
    print(f"7. asyncio.run worked: {result}")
except Exception as e:
    print(f"asyncio error: {e}")

print("8. All tests complete")