#!/usr/bin/env python3
"""
Monitor intelligent orchestrator execution in real-time
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

def monitor_session(session_id=None):
    """Monitor the execution of the intelligent orchestrator"""
    
    print("=" * 80)
    print("EXECUTION MONITOR - Real-Time Status")
    print("=" * 80)
    print()
    
    # Find the latest session if not specified
    sessions_dir = Path("sessions")
    
    if session_id:
        session_file = sessions_dir / f"session_{session_id}_*.json"
    else:
        # Get the most recent session
        session_files = sorted(sessions_dir.glob("session_*.json"), 
                              key=lambda x: x.stat().st_mtime, 
                              reverse=True)
        if not session_files:
            print("[ERROR] No session files found")
            return
        session_file = session_files[0]
        print(f"Monitoring: {session_file.name}")
    
    # Track agent states
    agent_states = {}
    agent_start_times = {}
    parallel_groups = []
    current_parallel = set()
    
    print("\nExecution Timeline:")
    print("-" * 80)
    
    last_size = 0
    no_change_count = 0
    
    while True:
        try:
            # Check if file has grown
            current_size = session_file.stat().st_size
            
            if current_size == last_size:
                no_change_count += 1
                if no_change_count > 10:  # No changes for 10 seconds
                    print("\n[INFO] No new activity for 10 seconds")
                    break
            else:
                no_change_count = 0
                last_size = current_size
            
            # Read new lines
            with open(session_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Parse each line
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    event = json.loads(line)
                    timestamp = event.get('timestamp', '')
                    agent = event.get('agent_name', '')
                    event_type = event.get('event_type', '')
                    
                    # Parse time
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    else:
                        time_str = "??:??:??"
                    
                    # Track agent events
                    if event_type == 'agent_start':
                        if agent not in agent_states:
                            agent_states[agent] = 'RUNNING'
                            agent_start_times[agent] = dt
                            
                            # Check for parallel execution
                            running_agents = [a for a, s in agent_states.items() if s == 'RUNNING']
                            if len(running_agents) > 1:
                                print(f"{time_str} [PARALLEL] {running_agents}")
                                current_parallel = set(running_agents)
                            else:
                                print(f"{time_str} [SEQUENTIAL] {agent} started")
                    
                    elif event_type == 'agent_complete':
                        if agent in agent_states:
                            agent_states[agent] = 'COMPLETED'
                            
                            # Calculate duration
                            if agent in agent_start_times:
                                duration = (dt - agent_start_times[agent]).total_seconds()
                                print(f"{time_str} [COMPLETED] {agent} ({duration:.1f}s)")
                            else:
                                print(f"{time_str} [COMPLETED] {agent}")
                            
                            # Remove from current parallel group
                            current_parallel.discard(agent)
                    
                    elif event_type == 'error' and agent:
                        agent_states[agent] = 'FAILED'
                        print(f"{time_str} [FAILED] {agent}")
                        current_parallel.discard(agent)
                        
                except json.JSONDecodeError:
                    continue
            
            # Show current status
            print("\r", end="")
            running = [a for a, s in agent_states.items() if s == 'RUNNING']
            completed = [a for a, s in agent_states.items() if s == 'COMPLETED']
            failed = [a for a, s in agent_states.items() if s == 'FAILED']
            
            status_line = f"Running: {len(running)} | Completed: {len(completed)} | Failed: {len(failed)}"
            print(f"\r{status_line}", end="", flush=True)
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n[STOPPED] Monitoring cancelled")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            break
    
    # Final summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    
    completed = [a for a, s in agent_states.items() if s == 'COMPLETED']
    failed = [a for a, s in agent_states.items() if s == 'FAILED']
    running = [a for a, s in agent_states.items() if s == 'RUNNING']
    
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Still Running: {running}")
    
    # Calculate total time
    if agent_start_times:
        first_start = min(agent_start_times.values())
        last_time = datetime.now()
        total_time = (last_time - first_start).total_seconds()
        print(f"Total execution time: {total_time:.1f} seconds")

if __name__ == "__main__":
    import sys
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    monitor_session(session_id)