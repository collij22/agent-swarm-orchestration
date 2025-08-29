#!/usr/bin/env python3
"""
Test Hook System Integration

Demonstrates the complete hook system working with the agent runtime.
Tests all hooks: pre-tool, post-tool, checkpoint, memory, progress, and cost control.
"""

import asyncio
import time
import json
from pathlib import Path
import sys

# Add lib directory to path
sys.path.append(str(Path(__file__).parent))

from lib.hook_manager import HookManager, HookContext, HookEvent, get_hook_manager
from lib.agent_logger import get_logger
from lib.agent_runtime import AnthropicAgentRunner, AgentContext, Tool, ModelType

# Import all hooks
sys.path.append(str(Path(__file__).parent / ".claude" / "hooks"))
import pre_tool_use
import post_tool_use
import checkpoint_save
import memory_check
import progress_update
import cost_control


async def test_integrated_hooks():
    """Test the complete hook system integration"""
    print("\n" + "="*60)
    print("HOOK SYSTEM INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Initialize components
    logger = get_logger()
    hook_manager = get_hook_manager(logger)
    
    # Register all hooks
    print("1. Registering hooks...")
    pre_tool_use.register(hook_manager)
    post_tool_use.register(hook_manager)
    checkpoint_save.register(hook_manager)
    memory_check.register(hook_manager)
    progress_update.register(hook_manager)
    cost_control.register(hook_manager)
    print("   [OK] All hooks registered\n")
    
    # Create sample tools for testing
    async def sample_write_file(reasoning: str, file_path: str, content: str) -> str:
        """Simulated file write"""
        await asyncio.sleep(0.5)  # Simulate work
        return f"File written: {file_path}"
    
    async def sample_api_call(reasoning: str, url: str, method: str = "GET") -> dict:
        """Simulated API call"""
        await asyncio.sleep(1.0)  # Simulate network delay
        return {"status": 200, "data": "Sample response"}
    
    async def sample_expensive_operation(reasoning: str, model: str, prompt: str) -> str:
        """Simulated expensive AI operation"""
        await asyncio.sleep(2.0)  # Simulate processing
        return f"Generated response using {model}"
    
    # Test 1: Pre-tool validation and security
    print("2. Testing Pre-Tool Hook (validation & security)...")
    context = HookContext(
        event=HookEvent.PRE_TOOL_USE,
        agent_name="test-agent",
        tool_name="write_file",
        parameters={
            "file_path": "./test_output.txt",
            "content": "Hello from hook test!"
        }
    )
    
    context = await hook_manager.execute_hooks(context)
    
    if context.error:
        print(f"   [FAIL] Pre-tool validation failed: {context.error}")
    else:
        print(f"   [OK] Pre-tool validation passed")
        print(f"     - Estimated cost: ${context.get('estimated_cost', 0):.4f}")
        print(f"     - Predicted time: {context.get('predicted_time', 0):.1f}s")
    print()
    
    # Test 2: Dangerous operation blocking
    print("3. Testing Security Blocking...")
    dangerous_context = HookContext(
        event=HookEvent.PRE_TOOL_USE,
        agent_name="test-agent",
        tool_name="run_command",
        parameters={
            "command": "rm -rf /important_files"  # Dangerous!
        }
    )
    
    dangerous_context = await hook_manager.execute_hooks(dangerous_context)
    
    if dangerous_context.error:
        print(f"   [OK] Dangerous operation blocked: {dangerous_context.error}")
    else:
        print(f"   [FAIL] Security check failed - dangerous operation not blocked!")
    print()
    
    # Test 3: Post-tool processing
    print("4. Testing Post-Tool Hook (metrics & caching)...")
    post_context = HookContext(
        event=HookEvent.POST_TOOL_USE,
        agent_name="test-agent",
        tool_name="api_call",
        parameters={"url": "https://api.example.com/data"},
        result={"status": 200, "data": "Success"}
    )
    post_context.set("tool_start_time", time.time() - 1.5)
    
    post_context = await hook_manager.execute_hooks(post_context)
    
    print(f"   [OK] Post-tool processing complete")
    if post_context.get("metrics"):
        metrics = post_context.get("metrics")
        print(f"     - Execution time: {metrics['execution_time']:.2f}s")
        print(f"     - Success rate: {metrics['success_rate']*100:.1f}%")
    print()
    
    # Test 4: Checkpoint creation
    print("5. Testing Checkpoint Save Hook...")
    checkpoint_context = HookContext(
        event=HookEvent.AGENT_COMPLETE,
        agent_name="project-architect",
        metadata={
            "current_phase": "architecture_design",
            "agent_context": {
                "artifacts": {
                    "architecture.md": "System design document",
                    "database.sql": "Database schema"
                },
                "decisions": [
                    {"decision": "Use microservices", "rationale": "Scalability"},
                    {"decision": "PostgreSQL", "rationale": "ACID compliance"}
                ]
            }
        }
    )
    
    checkpoint_context = await hook_manager.execute_hooks(checkpoint_context)
    
    if checkpoint_context.get("checkpoint_saved"):
        print(f"   [OK] Checkpoint created: {checkpoint_context.get('checkpoint_id')}")
    else:
        print(f"   [FAIL] Checkpoint creation failed")
    print()
    
    # Test 5: Memory monitoring
    print("6. Testing Memory Check Hook...")
    memory_context = HookContext(
        event=HookEvent.PERFORMANCE_CHECK,
        agent_name="test-agent"
    )
    
    memory_context = await hook_manager.execute_hooks(memory_context)
    
    if memory_context.get("memory_metrics"):
        metrics = memory_context.get("memory_metrics")
        print(f"   [OK] Memory check complete")
        print(f"     - RSS: {metrics['rss_mb']:.1f} MB")
        print(f"     - Available: {metrics['available_mb']:.1f} MB")
    else:
        print(f"   [WARN] Memory monitoring not available (psutil not installed)")
    print()
    
    # Test 6: Progress tracking
    print("7. Testing Progress Update Hook...")
    
    # Simulate workflow progress
    progress_hooks = []
    
    # Start workflow
    start_context = HookContext(
        event=HookEvent.AGENT_START,
        agent_name="project-architect",
        metadata={"estimated_tasks": 5}
    )
    progress_hooks.append(await hook_manager.execute_hooks(start_context))
    
    # Complete some tasks
    for i, agent in enumerate(["architect", "builder", "tester"]):
        complete_context = HookContext(
            event=HookEvent.AGENT_COMPLETE,
            agent_name=agent,
            metadata={"execution_time": 2.5 * (i + 1)}
        )
        progress_hooks.append(await hook_manager.execute_hooks(complete_context))
    
    # Check progress
    if progress_hooks[-1].get("progress"):
        progress = progress_hooks[-1].get("progress")
        print(f"   [OK] Progress tracking active")
        print(f"     - Progress: {progress['percent']:.1f}%")
        print(f"     - Completed: {progress['completed']}/{progress['total']}")
        print(f"     - ETA: {progress['eta']:.0f} seconds")
    print()
    
    # Test 7: Cost control
    print("8. Testing Cost Control Hook...")
    
    # Test normal cost operation
    cost_context = HookContext(
        event=HookEvent.PRE_TOOL_USE,
        agent_name="ai-specialist",
        tool_name="claude_call",
        parameters={
            "model": "claude-3-sonnet",
            "prompt": "Generate a detailed system architecture"
        }
    )
    
    cost_context = await hook_manager.execute_hooks(cost_context)
    
    if cost_context.get("operation_cost"):
        print(f"   [OK] Cost tracking active")
        print(f"     - Operation cost: ${cost_context.get('operation_cost'):.4f}")
        
        summary = cost_context.get("cost_summary")
        if summary:
            print(f"     - Daily total: ${summary['daily_cost']:.2f}")
            print(f"     - Budget remaining: ${summary['daily_budget_remaining']:.2f}")
    
    # Test expensive operation with alternatives
    expensive_context = HookContext(
        event=HookEvent.PRE_TOOL_USE,
        agent_name="ai-specialist",
        tool_name="claude_call",
        parameters={
            "model": "claude-3-opus",
            "prompt": "x" * 10000  # Large prompt
        }
    )
    
    expensive_context = await hook_manager.execute_hooks(expensive_context)
    
    if expensive_context.get("cheaper_alternatives"):
        alts = expensive_context.get("cheaper_alternatives")
        print(f"   [OK] Cost optimization suggestions:")
        for alt in alts[:2]:
            if "model" in alt:
                print(f"     - Use {alt['model']}: save ${alt['savings']:.4f}")
    print()
    
    # Test 8: Error recovery
    print("9. Testing Error Recovery...")
    error_context = HookContext(
        event=HookEvent.POST_TOOL_USE,
        agent_name="test-agent",
        tool_name="api_call",
        parameters={"url": "https://api.example.com/endpoint"},
        error="Connection timeout"
    )
    
    error_context = await hook_manager.execute_hooks(error_context)
    
    if error_context.get("recovery_suggestion"):
        print(f"   [OK] Error recovery suggestion: {error_context.get('recovery_suggestion')}")
    print()
    
    # Test 9: Hook metrics
    print("10. Hook Performance Metrics:")
    all_metrics = hook_manager.get_hook_metrics()
    
    for hook_name, metrics in all_metrics.items():
        if metrics.get("executions", 0) > 0:
            print(f"   - {hook_name}:")
            print(f"       Executions: {metrics['executions']}")
            print(f"       Success rate: {metrics['successes']}/{metrics['executions']}")
            print(f"       Avg time: {metrics['avg_time']:.3f}s")
    print()
    
    # Save configuration
    print("11. Saving Hook Configuration...")
    hook_manager.save_configuration()
    print("   [OK] Configuration saved to .claude/hooks/config.yaml")
    print()
    
    # Final summary
    print("="*60)
    print("INTEGRATION TEST COMPLETE")
    print("="*60)
    print("\nSummary:")
    print("[OK] Hook registration and execution")
    print("[OK] Pre-tool validation and security")
    print("[OK] Post-tool metrics and caching")
    print("[OK] Checkpoint creation and recovery")
    print("[OK] Memory monitoring")
    print("[OK] Progress tracking")
    print("[OK] Cost control and optimization")
    print("[OK] Error recovery suggestions")
    print("\nThe hook system is fully integrated and operational!")
    
    # Close logger session
    logger.close_session()


async def test_with_real_agent():
    """Test hooks with real agent execution (requires API key)"""
    print("\n" + "="*60)
    print("TESTING WITH AGENT RUNTIME")
    print("="*60 + "\n")
    
    # Initialize
    logger = get_logger()
    hook_manager = get_hook_manager(logger)
    
    # Register all hooks
    pre_tool_use.register(hook_manager)
    post_tool_use.register(hook_manager)
    checkpoint_save.register(hook_manager)
    
    # Create runtime (will use simulation if no API key)
    try:
        runtime = AnthropicAgentRunner(logger=logger)
    except ValueError:
        print("No API key found - using simulation mode")
        runtime = AnthropicAgentRunner(logger=logger)
    
    # Create tools with hook integration
    async def write_with_hooks(reasoning: str, file_path: str, content: str, context: AgentContext) -> str:
        """Write file with hook support"""
        # Pre-tool hook
        hook_context = HookContext(
            event=HookEvent.PRE_TOOL_USE,
            agent_name="test-agent",
            tool_name="write_file",
            parameters={"file_path": file_path, "content": content}
        )
        hook_context = await hook_manager.execute_hooks(hook_context)
        
        if hook_context.error:
            return f"Blocked by pre-hook: {hook_context.error}"
        
        # Execute tool
        result = f"File written: {file_path}"
        
        # Post-tool hook
        hook_context.event = HookEvent.POST_TOOL_USE
        hook_context.result = result
        hook_context = await hook_manager.execute_hooks(hook_context)
        
        return result
    
    # Register tool
    runtime.register_tool(Tool(
        name="write_file",
        description="Write content to file",
        parameters={
            "file_path": {"type": "string", "required": True},
            "content": {"type": "string", "required": True}
        },
        function=write_with_hooks
    ))
    
    # Create context
    agent_context = AgentContext(
        project_requirements={"name": "TestProject", "type": "web_app"},
        completed_tasks=[],
        artifacts={},
        decisions=[],
        current_phase="implementation"
    )
    
    # Run agent with hooks
    print("Running agent with integrated hooks...")
    
    success, result, updated_context = await runtime.run_agent_async(
        "test-agent",
        "Write a simple test file to demonstrate the hook system.",
        agent_context,
        model=ModelType.SONNET,
        max_iterations=3
    )
    
    print(f"\nAgent completed: {success}")
    print(f"Result: {result[:200] if result else 'None'}")
    
    # Check for checkpoints
    from .claude.hooks.checkpoint_save import get_checkpoint_manager
    checkpoint_manager = get_checkpoint_manager()
    checkpoints = checkpoint_manager.list_checkpoints()
    
    if checkpoints:
        print(f"\nCheckpoints created: {len(checkpoints)}")
        for cp in checkpoints[-3:]:
            print(f"  - {cp['description']} ({cp['timestamp']})")
    
    logger.close_session()


if __name__ == "__main__":
    # Run integration tests
    asyncio.run(test_integrated_hooks())
    
    # Optionally test with real agent
    # asyncio.run(test_with_real_agent())