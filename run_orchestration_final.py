#!/usr/bin/env python
"""Final solution for running orchestration without I/O issues"""

import sys
import os
import asyncio
import io
from pathlib import Path

# Ensure UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

def setup_safe_io():
    """Setup safe I/O wrappers that won't close"""
    import builtins
    
    # Store original stdout/stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    class PersistentStream:
        """Stream wrapper that prevents closing"""
        def __init__(self, stream, name):
            self.stream = stream
            self.name = name
            self.encoding = 'utf-8'
            self.errors = 'replace'
            self.closed = False
            
        def write(self, data):
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='replace')
            try:
                if self.stream and not getattr(self.stream, 'closed', False):
                    return self.stream.write(data)
                else:
                    # Fallback to original stdout
                    return original_stdout.write(data)
            except:
                # Silently ignore write errors
                return len(data) if data else 0
                
        def flush(self):
            try:
                if self.stream and hasattr(self.stream, 'flush'):
                    self.stream.flush()
            except:
                pass
                
        def close(self):
            # Never actually close
            pass
            
        def fileno(self):
            try:
                return self.stream.fileno()
            except:
                return 1 if 'out' in self.name else 2
                
        def isatty(self):
            try:
                return self.stream.isatty()
            except:
                return False
                
        def __getattr__(self, name):
            # Delegate other attributes
            return getattr(self.stream, name, None)
    
    # Replace stdout/stderr with persistent versions
    sys.stdout = PersistentStream(sys.stdout, 'stdout')
    sys.stderr = PersistentStream(sys.stderr, 'stderr')
    
    # Monkey-patch Rich Console to handle our streams
    try:
        from rich import console as rich_console
        original_console_init = rich_console.Console.__init__
        
        def patched_console_init(self, *args, **kwargs):
            # Force safe file handles
            kwargs['file'] = sys.stdout
            kwargs['force_terminal'] = False
            kwargs['force_jupyter'] = False
            kwargs['force_interactive'] = False
            original_console_init(self, *args, **kwargs)
            
        rich_console.Console.__init__ = patched_console_init
    except ImportError:
        pass

def patch_logger_creation():
    """Patch the logger creation to handle I/O issues"""
    try:
        from lib import agent_logger
        
        original_create = agent_logger.create_new_session
        
        def safe_create_session(session_id, enable_human_log, summary_level):
            """Create session with I/O protection"""
            try:
                # Ensure stdout is available
                if not hasattr(sys, 'stdout') or sys.stdout is None:
                    setup_safe_io()
                    
                return original_create(session_id, enable_human_log, summary_level)
            except Exception as e:
                print(f"Warning: Logger creation issue ({e}), using fallback")
                
                # Return a minimal logger
                class MinimalLogger:
                    def __init__(self):
                        self.session_id = session_id
                        
                    def log_reasoning(self, *args, **kwargs):
                        pass
                        
                    def log_agent_start(self, *args, **kwargs):
                        print(f"Starting agent: {kwargs.get('agent_name', 'unknown')}")
                        
                    def log_agent_end(self, *args, **kwargs):
                        print(f"Agent completed: {kwargs.get('agent_name', 'unknown')}")
                        
                    def log_tool_use(self, *args, **kwargs):
                        pass
                        
                    def log_error(self, *args, **kwargs):
                        print(f"Error: {kwargs.get('error', 'unknown')}")
                        
                    def close_session(self, *args, **kwargs):
                        pass
                        
                    def get_session_data(self):
                        return {}
                        
                    def __getattr__(self, name):
                        return lambda *args, **kwargs: None
                        
                return MinimalLogger()
                
        agent_logger.create_new_session = safe_create_session
    except ImportError:
        pass

async def run_orchestration():
    """Run the orchestration with proper initialization"""
    # Setup safe I/O first
    setup_safe_io()
    
    # Patch logger creation
    patch_logger_creation()
    
    # Now import and run orchestrate_enhanced
    from orchestrate_enhanced import main
    
    # Set command line arguments
    sys.argv = [
        'orchestrate_enhanced.py',
        '--project-type', 'full_stack_api',
        '--requirements', 'projects/quickshop-mvp-test/requirements.yaml',
        '--output-dir', 'projects/quickshop-mvp-test6',
        '--progress',
        '--summary-level', 'concise',
        '--max-parallel', '2',
        '--human-log'
    ]
    
    print("=" * 60)
    print("Starting Enhanced Orchestration (Final Fix)")
    print("=" * 60)
    
    try:
        result = await main()
        print("\n" + "=" * 60)
        print("Orchestration completed successfully!")
        return result
    except Exception as e:
        print(f"\nOrchestration error: {e}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main entry point"""
    # Setup I/O before anything else
    setup_safe_io()
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the orchestration
        loop.run_until_complete(run_orchestration())
    except KeyboardInterrupt:
        print("\nOrchestration interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        return 1
    finally:
        # Clean up loop
        try:
            loop.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit(main())