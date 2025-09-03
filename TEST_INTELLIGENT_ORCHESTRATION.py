#!/usr/bin/env python3
"""
Test the Intelligent Orchestrator with real-time monitoring
"""

import os
import sys
import asyncio
import subprocess
import threading
import time
from pathlib import Path
import json
from datetime import datetime

def monitor_execution():
    """Monitor the orchestrator execution in a separate thread"""
    print("\n" + "="*80)
    print("REAL-TIME EXECUTION MONITOR")
    print("="*80)
    
    # Wait for session file to be created
    sessions_dir = Path("sessions")
    sessions_dir.mkdir(exist_ok=True)
    
    # Get the latest session file
    start_time = time.time()
    session_file = None
    
    while time.time() - start_time < 10:  # Wait up to 10 seconds
        session_files = list(sessions_dir.glob("session_*.json"))
        if session_files:
            # Get the most recent file
            session_file = max(session_files, key=lambda x: x.stat().st_mtime)
            if session_file.stat().st_mtime > start_time:
                print(f"Monitoring session: {session_file.name}")
                break
        time.sleep(0.5)
    
    if not session_file:
        print("[WARNING] No new session file found")
        return
    
    # Monitor the session
    last_size = 0
    agent_status = {}
    parallel_groups = []
    
    while True:
        try:
            current_size = session_file.stat().st_size
            
            if current_size > last_size:
                with open(session_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Parse new lines
                for line in lines[len(agent_status):]:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line)
                        agent = event.get('agent_name', '')
                        event_type = event.get('event_type', '')
                        timestamp = event.get('timestamp', '')
                        
                        if event_type == 'agent_start':
                            agent_status[agent] = 'RUNNING'
                            
                            # Check for parallel execution
                            running = [a for a, s in agent_status.items() if s == 'RUNNING']
                            if len(running) > 1:
                                print(f"\n[PARALLEL] {running}")
                            else:
                                print(f"\n[SEQUENTIAL] {agent} started")
                        
                        elif event_type == 'agent_complete':
                            agent_status[agent] = 'COMPLETED'
                            print(f"[COMPLETED] {agent}")
                        
                        elif event_type == 'error' and agent:
                            agent_status[agent] = 'FAILED'
                            print(f"[FAILED] {agent}")
                    
                    except json.JSONDecodeError:
                        continue
                
                last_size = current_size
            
            # Check if all agents are done
            if len(agent_status) >= 8:  # We expect 8 agents
                if all(s in ['COMPLETED', 'FAILED'] for s in agent_status.values()):
                    print("\n[MONITOR] All agents finished")
                    break
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] Monitor error: {e}")
            break
    
    # Final summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    completed = [a for a, s in agent_status.items() if s == 'COMPLETED']
    failed = [a for a, s in agent_status.items() if s == 'FAILED']
    print(f"Completed: {len(completed)} agents")
    print(f"Failed: {len(failed)} agents")
    
    if failed:
        print(f"Failed agents: {failed}")

def main():
    """Main test execution"""
    print("="*80)
    print("INTELLIGENT ORCHESTRATION TEST")
    print("="*80)
    print()
    
    # Check API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("[ERROR] ANTHROPIC_API_KEY not set!")
        print("Set it with: set ANTHROPIC_API_KEY=your-key-here")
        return
    
    print("Starting test with intelligent dependency resolution...")
    print()
    print("Expected execution pattern:")
    print("  1. requirements-analyst (solo)")
    print("  2. project-architect (solo, waits for requirements)")
    print("  3. [PARALLEL] database-expert, rapid-builder, frontend-specialist")
    print("  4. api-integrator (solo, waits for backend+frontend)")
    print("  5. [PARALLEL] devops-engineer, quality-guardian")
    print()
    
    # Start monitor in background thread
    monitor_thread = threading.Thread(target=monitor_execution, daemon=True)
    monitor_thread.start()
    
    # Run the intelligent orchestrator
    print("Starting orchestrator...")
    start_time = time.time()
    
    try:
        # Run the orchestrator
        result = subprocess.run(
            [sys.executable, "INTELLIGENT_ORCHESTRATOR.py"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        execution_time = time.time() - start_time
        
        print("\n" + "="*80)
        print(f"Execution completed in {execution_time:.2f} seconds")
        
        # Check output directory
        output_dir = Path("projects/quickshop-mvp-intelligent")
        if output_dir.exists():
            files = list(output_dir.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            print(f"Files created: {file_count}")
            
            if file_count > 0:
                print("\nSample files created:")
                for i, f in enumerate(files[:10]):
                    if f.is_file():
                        print(f"  - {f.relative_to(output_dir)}")
                if file_count > 10:
                    print(f"  ... and {file_count - 10} more files")
        
        # Compare with sequential time
        sequential_time = 30 * 8  # 8 agents at ~30 seconds each
        time_saved = sequential_time - execution_time
        percentage_saved = (time_saved / sequential_time) * 100
        
        print("\n" + "="*80)
        print("PERFORMANCE COMPARISON")
        print("="*80)
        print(f"Sequential (estimated): {sequential_time}s")
        print(f"Intelligent (actual): {execution_time:.2f}s")
        print(f"Time saved: {time_saved:.2f}s ({percentage_saved:.1f}% faster)")
        
        # Wait for monitor thread
        monitor_thread.join(timeout=5)
        
    except Exception as e:
        print(f"\n[ERROR] Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()