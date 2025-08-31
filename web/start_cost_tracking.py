#!/usr/bin/env python3
"""
Start Cost Tracking Service
Launches the cost tracking API and integrates with the dashboard

This script:
1. Starts the cost tracking API server
2. Integrates with the existing dashboard
3. Monitors real-time costs
4. Provides budget alerts
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
import webbrowser
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required = ["fastapi", "uvicorn", "sqlite3"]
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        logger.warning(f"Missing dependencies: {missing}")
        logger.info("Installing missing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], check=True)
    
    return True

def update_dashboard_config():
    """Update dashboard configuration to include cost tracking"""
    dashboard_config_path = Path("web/dashboard/src/config.ts")
    
    if dashboard_config_path.exists():
        logger.info("Updating dashboard configuration...")
        
        # Read existing config
        with open(dashboard_config_path, 'r') as f:
            config = f.read()
        
        # Add cost tracking API endpoint if not present
        if "COST_API_URL" not in config:
            cost_config = """
// Cost Tracking API
export const COST_API_URL = process.env.REACT_APP_COST_API_URL || 'http://localhost:8001';
export const COST_WS_URL = process.env.REACT_APP_COST_WS_URL || 'ws://localhost:8001/ws/costs';

// Budget Settings
export const DEFAULT_BUDGET_LIMITS = {
  hourly: 10,
  daily: 100,
  monthly: 2000
};

// Refresh Settings
export const COST_REFRESH_INTERVAL = 5000; // 5 seconds
"""
            
            # Append to config
            with open(dashboard_config_path, 'a') as f:
                f.write("\n" + cost_config)
            
            logger.info("Dashboard configuration updated")
    else:
        # Create new config
        dashboard_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_content = """
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

// Cost Tracking API
export const COST_API_URL = process.env.REACT_APP_COST_API_URL || 'http://localhost:8001';
export const COST_WS_URL = process.env.REACT_APP_COST_WS_URL || 'ws://localhost:8001/ws/costs';

// Budget Settings
export const DEFAULT_BUDGET_LIMITS = {
  hourly: 10,
  daily: 100,
  monthly: 2000
};

// Refresh Settings
export const COST_REFRESH_INTERVAL = 5000; // 5 seconds
"""
        
        with open(dashboard_config_path, 'w') as f:
            f.write(config_content)
        
        logger.info("Created dashboard configuration")

def add_cost_route_to_dashboard():
    """Add cost tracking route to the dashboard"""
    app_path = Path("web/dashboard/src/App.tsx")
    
    if app_path.exists():
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check if CostTracker is already imported
        if "CostTracker" not in content:
            logger.info("Adding cost tracking to dashboard routes...")
            
            # Add import
            import_line = "import CostTracker from './components/CostTracker';"
            
            # Find imports section
            import_index = content.find("import")
            if import_index != -1:
                # Find the end of imports
                last_import = content.rfind("import", 0, content.find("function App") or content.find("const App"))
                if last_import != -1:
                    # Find the end of the line
                    end_of_line = content.find("\n", last_import)
                    # Insert new import
                    content = content[:end_of_line] + "\n" + import_line + content[end_of_line:]
            
            # Add route
            route_line = '          <Route path="/costs" element={<CostTracker />} />'
            
            # Find routes section
            routes_index = content.find("<Routes>")
            if routes_index != -1:
                # Find a good place to insert (before </Routes>)
                end_routes = content.find("</Routes>", routes_index)
                if end_routes != -1:
                    # Insert before </Routes>
                    content = content[:end_routes] + route_line + "\n        " + content[end_routes:]
            
            # Save updated content
            with open(app_path, 'w') as f:
                f.write(content)
            
            logger.info("Cost tracking route added to dashboard")

def create_startup_script():
    """Create a unified startup script"""
    script_content = '''#!/usr/bin/env python3
"""
Unified Dashboard and Cost Tracking Startup Script
"""

import subprocess
import time
import webbrowser
import sys
import os
from pathlib import Path

def start_services():
    """Start all required services"""
    
    print("Starting Agent Swarm Dashboard with Cost Tracking...")
    print("=" * 50)
    
    # Start main API server
    print("Starting main API server...")
    api_process = subprocess.Popen(
        [sys.executable, "web/start_dashboard.py"],
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start cost tracking API
    print("Starting cost tracking API...")
    cost_process = subprocess.Popen(
        [sys.executable, "web/api/cost_tracking_api.py"],
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for services to start
    time.sleep(3)
    
    # Check if services are running
    if api_process.poll() is None and cost_process.poll() is None:
        print("\\nServices started successfully!")
        print("\\nAccess points:")
        print("  Dashboard: http://localhost:5173")
        print("  Main API: http://localhost:8000/docs")
        print("  Cost API: http://localhost:8001/docs")
        print("  Cost Tracking: http://localhost:5173/costs")
        print("\\nPress Ctrl+C to stop all services")
        
        # Open browser
        webbrowser.open("http://localhost:5173/costs")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\\nStopping services...")
            api_process.terminate()
            cost_process.terminate()
            print("Services stopped")
    else:
        print("Failed to start services")
        if api_process.poll() is not None:
            print("Main API failed to start")
        if cost_process.poll() is not None:
            print("Cost API failed to start")
        sys.exit(1)

if __name__ == "__main__":
    start_services()
'''
    
    script_path = Path("web/start_with_cost_tracking.py")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix
    if os.name != 'nt':
        os.chmod(script_path, 0o755)
    
    logger.info(f"Created unified startup script: {script_path}")
    
    # Also create a batch file for Windows
    if os.name == 'nt':
        batch_content = f'''@echo off
echo Starting Agent Swarm Dashboard with Cost Tracking...
echo ==================================================
python "{script_path}"
pause
'''
        batch_path = Path("web/start_with_cost_tracking.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        logger.info(f"Created Windows batch file: {batch_path}")

async def test_cost_tracking():
    """Test the cost tracking system"""
    logger.info("Testing cost tracking system...")
    
    # Import the API
    sys.path.append(str(Path.cwd()))
    from web.api.cost_tracking_api import cost_tracker, CostEntry
    
    # Add some test data
    import random
    from datetime import datetime, timedelta
    
    providers = ["anthropic", "openai", "gemini"]
    models = ["claude-3-5-sonnet", "gpt-4", "gemini-pro"]
    agents = ["rapid-builder", "frontend-specialist", "quality-guardian", "database-expert"]
    
    # Generate test data for the last 24 hours
    now = datetime.now()
    for i in range(100):
        hours_ago = random.randint(0, 24)
        timestamp = now - timedelta(hours=hours_ago)
        
        entry = CostEntry(
            timestamp=int(timestamp.timestamp()),
            provider=random.choice(providers),
            model=random.choice(models),
            agent=random.choice(agents),
            inputTokens=random.randint(100, 1000),
            outputTokens=random.randint(200, 2000),
            cost=random.uniform(0.001, 0.05),
            cached=random.random() > 0.7
        )
        
        cost_tracker.add_cost(entry)
    
    logger.info("Added 100 test cost entries")
    
    # Get summary
    summary = cost_tracker.get_summary("day")
    logger.info(f"Daily cost summary: ${summary.total_cost:.4f} across {summary.total_requests} requests")
    logger.info(f"Cache savings: ${summary.cache_savings:.4f}")

def main():
    """Main entry point"""
    print("""
    ========================================================
           Cost Tracking Integration for Agent Swarm
    ========================================================
    """)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Failed to install dependencies")
        sys.exit(1)
    
    # Update dashboard configuration
    update_dashboard_config()
    
    # Add cost tracking route
    add_cost_route_to_dashboard()
    
    # Create unified startup script
    create_startup_script()
    
    print("""
    ========================================================
                  Cost Tracking Setup Complete!
    ========================================================
    
    The cost tracking system has been integrated with your dashboard.
    
    To start the enhanced dashboard with cost tracking:
    
    Windows:
      web\\start_with_cost_tracking.bat
    
    Linux/Mac:
      python web/start_with_cost_tracking.py
    
    Features added:
    - Real-time cost monitoring
    - Provider cost breakdown
    - Agent-level cost analysis
    - Budget alerts and limits
    - Cost optimization recommendations
    - Historical cost trends
    - Export capabilities (CSV/JSON)
    
    Access the cost tracking dashboard at:
      http://localhost:5173/costs
    
    API Documentation:
      http://localhost:8001/docs
    """)
    
    # Ask if user wants to start now
    response = input("\nDo you want to start the dashboard now? (y/n): ")
    if response.lower() == 'y':
        logger.info("Starting dashboard with cost tracking...")
        subprocess.run([sys.executable, "web/start_with_cost_tracking.py"])

if __name__ == "__main__":
    main()