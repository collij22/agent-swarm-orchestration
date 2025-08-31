#!/usr/bin/env python3
"""
Cost Tracking API for Web Dashboard
Provides real-time cost metrics and analytics

Features:
- Real-time cost data streaming
- Historical cost analysis
- Provider-specific metrics
- Agent-level cost breakdown
- Budget monitoring and alerts
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import asyncio
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import logging

# Import LLM provider integration
try:
    from lib.llm_providers import get_cache, MultiLLMOrchestrator
    from lib.llm_integration import EnhancedAgentRunner
except ImportError:
    print("Warning: LLM modules not found. Using mock data.")
    get_cache = None
    MultiLLMOrchestrator = None
    EnhancedAgentRunner = None

app = FastAPI(title="Cost Tracking API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path("data/cost_tracking.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the cost tracking database"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cost_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                agent TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                cached INTEGER NOT NULL,
                session_id TEXT,
                request_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                limit_type TEXT NOT NULL,
                amount REAL NOT NULL,
                period TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                threshold REAL NOT NULL,
                current_value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

# Initialize database on startup
init_database()

class CostEntry(BaseModel):
    """Model for cost tracking entries"""
    timestamp: int
    provider: str
    model: str
    agent: str
    input_tokens: int = Field(alias="inputTokens")
    output_tokens: int = Field(alias="outputTokens")
    cost: float
    cached: bool
    session_id: Optional[str] = Field(None, alias="sessionId")
    request_id: Optional[str] = Field(None, alias="requestId")

class BudgetLimit(BaseModel):
    """Model for budget limits"""
    limit_type: str = Field(alias="limitType")
    amount: float
    period: str

class CostSummary(BaseModel):
    """Model for cost summary response"""
    total_cost: float = Field(alias="totalCost")
    total_tokens: int = Field(alias="totalTokens")
    total_requests: int = Field(alias="totalRequests")
    cache_savings: float = Field(alias="cacheSavings")
    average_cost_per_request: float = Field(alias="averageCostPerRequest")
    provider_costs: Dict[str, float] = Field(alias="providerCosts")
    agent_costs: Dict[str, float] = Field(alias="agentCosts")
    hourly_data: List[Dict[str, Any]] = Field(alias="hourlyData")
    daily_data: List[Dict[str, Any]] = Field(alias="dailyData")

# In-memory cost tracker for real-time updates
class CostTracker:
    def __init__(self):
        self.recent_costs: List[CostEntry] = []
        self.websocket_clients: List[WebSocket] = []
        self.budget_limits = {
            "hourly": 10.0,
            "daily": 100.0,
            "monthly": 2000.0
        }
        self.current_usage = {
            "hourly": 0.0,
            "daily": 0.0,
            "monthly": 0.0
        }
    
    def add_cost(self, entry: CostEntry):
        """Add a new cost entry"""
        self.recent_costs.append(entry)
        
        # Keep only last 1000 entries in memory
        if len(self.recent_costs) > 1000:
            self.recent_costs = self.recent_costs[-1000:]
        
        # Update current usage
        self.update_usage(entry.cost)
        
        # Check budget alerts
        self.check_budget_alerts()
        
        # Store in database
        self.store_in_database(entry)
        
        # Notify WebSocket clients
        asyncio.create_task(self.broadcast_update(entry))
    
    def update_usage(self, cost: float):
        """Update current usage tracking"""
        self.current_usage["hourly"] += cost
        self.current_usage["daily"] += cost
        self.current_usage["monthly"] += cost
    
    def check_budget_alerts(self):
        """Check if any budget thresholds are exceeded"""
        alerts = []
        
        for period, limit in self.budget_limits.items():
            usage = self.current_usage[period]
            if usage > limit * 0.8:  # 80% threshold warning
                alert_type = "warning" if usage < limit else "critical"
                alerts.append({
                    "type": alert_type,
                    "period": period,
                    "usage": usage,
                    "limit": limit,
                    "percentage": (usage / limit) * 100
                })
        
        if alerts:
            self.store_alerts(alerts)
    
    def store_in_database(self, entry: CostEntry):
        """Store cost entry in database"""
        with get_db() as conn:
            conn.execute("""
                INSERT INTO cost_entries 
                (timestamp, provider, model, agent, input_tokens, output_tokens, cost, cached, session_id, request_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.timestamp,
                entry.provider,
                entry.model,
                entry.agent,
                entry.input_tokens,
                entry.output_tokens,
                entry.cost,
                1 if entry.cached else 0,
                entry.session_id,
                entry.request_id
            ))
            conn.commit()
    
    def store_alerts(self, alerts: List[Dict]):
        """Store budget alerts in database"""
        with get_db() as conn:
            for alert in alerts:
                conn.execute("""
                    INSERT INTO cost_alerts (alert_type, message, threshold, current_value)
                    VALUES (?, ?, ?, ?)
                """, (
                    alert["type"],
                    f"Budget {alert['type']} for {alert['period']} period",
                    alert["limit"],
                    alert["usage"]
                ))
            conn.commit()
    
    async def broadcast_update(self, entry: CostEntry):
        """Broadcast cost update to WebSocket clients"""
        message = {
            "type": "cost_update",
            "data": entry.dict()
        }
        
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except:
                self.websocket_clients.remove(client)
    
    def get_summary(self, time_range: str, provider: Optional[str] = None) -> CostSummary:
        """Get cost summary for specified time range"""
        # Calculate time window
        now = datetime.now()
        if time_range == "hour":
            start_time = now - timedelta(hours=1)
        elif time_range == "day":
            start_time = now - timedelta(days=1)
        elif time_range == "week":
            start_time = now - timedelta(weeks=1)
        else:  # month
            start_time = now - timedelta(days=30)
        
        start_timestamp = int(start_time.timestamp())
        
        # Query database
        with get_db() as conn:
            query = """
                SELECT * FROM cost_entries 
                WHERE timestamp > ?
            """
            params = [start_timestamp]
            
            if provider and provider != "all":
                query += " AND provider = ?"
                params.append(provider)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        # Calculate summary
        total_cost = 0
        total_tokens = 0
        cache_savings = 0
        provider_costs = {}
        agent_costs = {}
        hourly_data = {}
        daily_data = {}
        
        for row in rows:
            cost = row["cost"]
            
            if row["cached"]:
                cache_savings += cost
            else:
                total_cost += cost
            
            # Provider breakdown
            provider = row["provider"]
            if provider not in provider_costs:
                provider_costs[provider] = 0
            provider_costs[provider] += cost
            
            # Agent breakdown
            agent = row["agent"]
            if agent not in agent_costs:
                agent_costs[agent] = 0
            agent_costs[agent] += cost
            
            # Token count
            total_tokens += row["input_tokens"] + row["output_tokens"]
            
            # Time-based aggregation
            timestamp = datetime.fromtimestamp(row["timestamp"])
            hour_key = timestamp.strftime("%H:00")
            day_key = timestamp.strftime("%Y-%m-%d")
            
            if hour_key not in hourly_data:
                hourly_data[hour_key] = 0
            hourly_data[hour_key] += cost
            
            if day_key not in daily_data:
                daily_data[day_key] = 0
            daily_data[day_key] += cost
        
        # Format response
        return CostSummary(
            totalCost=total_cost,
            totalTokens=total_tokens,
            totalRequests=len(rows),
            cacheSavings=cache_savings,
            averageCostPerRequest=total_cost / len(rows) if rows else 0,
            providerCosts=provider_costs,
            agentCosts=agent_costs,
            hourlyData=[{"hour": k, "cost": v} for k, v in sorted(hourly_data.items())],
            dailyData=[{"date": k, "cost": v} for k, v in sorted(daily_data.items())]
        )

# Initialize global cost tracker
cost_tracker = CostTracker()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Cost Tracking API"}

@app.get("/api/costs")
async def get_costs(
    range: str = Query("day", description="Time range: hour, day, week, month"),
    provider: Optional[str] = Query("all", description="Provider filter")
):
    """Get cost data for specified time range"""
    try:
        summary = cost_tracker.get_summary(range, provider)
        
        # Get recent entries for the chart
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT * FROM cost_entries 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            recent_entries = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "summary": summary.dict(),
            "costs": recent_entries
        }
    except Exception as e:
        logger.error(f"Error fetching costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/costs")
async def add_cost(entry: CostEntry):
    """Add a new cost entry"""
    try:
        cost_tracker.add_cost(entry)
        return {"success": True, "message": "Cost entry added"}
    except Exception as e:
        logger.error(f"Error adding cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/budget")
async def get_budget():
    """Get current budget status"""
    return {
        "limits": cost_tracker.budget_limits,
        "usage": cost_tracker.current_usage,
        "alerts": []
    }

@app.put("/api/budget")
async def update_budget(limits: Dict[str, float]):
    """Update budget limits"""
    cost_tracker.budget_limits.update(limits)
    return {"success": True, "limits": cost_tracker.budget_limits}

@app.get("/api/optimization")
async def get_optimization_suggestions():
    """Get cost optimization suggestions"""
    suggestions = []
    
    # Analyze agent costs
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT agent, AVG(cost) as avg_cost, COUNT(*) as request_count
            FROM cost_entries
            WHERE timestamp > ?
            GROUP BY agent
            ORDER BY avg_cost DESC
        """, [int((datetime.now() - timedelta(days=7)).timestamp())])
        
        for row in cursor.fetchall():
            if row["avg_cost"] > 0.01:
                suggestions.append({
                    "agent": row["agent"],
                    "current_avg_cost": row["avg_cost"],
                    "recommendation": "Consider using a cheaper model for routine tasks",
                    "potential_savings": row["avg_cost"] * row["request_count"] * 0.5
                })
    
    # Check cache utilization
    if get_cache:
        cache = get_cache()
        stats = cache.get_stats()
        
        if float(stats["hit_rate"].strip("%")) < 50:
            suggestions.append({
                "type": "cache",
                "recommendation": "Increase cache TTL to improve hit rate",
                "current_hit_rate": stats["hit_rate"],
                "potential_savings": stats["cost_saved"] * 2
            })
    
    return {"suggestions": suggestions}

@app.websocket("/ws/costs")
async def websocket_costs(websocket: WebSocket):
    """WebSocket endpoint for real-time cost updates"""
    await websocket.accept()
    cost_tracker.websocket_clients.append(websocket)
    
    try:
        # Send initial data
        summary = cost_tracker.get_summary("day")
        await websocket.send_json({
            "type": "initial",
            "data": summary.dict()
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in cost_tracker.websocket_clients:
            cost_tracker.websocket_clients.remove(websocket)

@app.get("/api/export")
async def export_costs(
    format: str = Query("csv", description="Export format: csv or json"),
    range: str = Query("day", description="Time range")
):
    """Export cost data"""
    summary = cost_tracker.get_summary(range)
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Provider", "Model", "Agent", "Cost", "Cached"])
        
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM cost_entries ORDER BY timestamp DESC")
            for row in cursor.fetchall():
                writer.writerow([
                    datetime.fromtimestamp(row["timestamp"]).isoformat(),
                    row["provider"],
                    row["model"],
                    row["agent"],
                    row["cost"],
                    "Yes" if row["cached"] else "No"
                ])
        
        return JSONResponse(
            content={"data": output.getvalue()},
            headers={"Content-Disposition": "attachment; filename=costs.csv"}
        )
    else:
        return summary.dict()

# Integration with orchestrator
def integrate_cost_tracking():
    """Integrate cost tracking with the orchestrator"""
    if EnhancedAgentRunner:
        # Hook into agent runner to track costs
        original_run = EnhancedAgentRunner.run_agent_multi_llm
        
        async def tracked_run(self, *args, **kwargs):
            result = await original_run(self, *args, **kwargs)
            
            # Track the cost
            if result.get("success"):
                entry = CostEntry(
                    timestamp=int(datetime.now().timestamp()),
                    provider=result.get("provider", "unknown"),
                    model=result.get("model", "unknown"),
                    agent=result.get("agent", "unknown"),
                    inputTokens=result.get("usage", {}).get("input_tokens", 0),
                    outputTokens=result.get("usage", {}).get("output_tokens", 0),
                    cost=result.get("cost", 0),
                    cached=result.get("cached", False)
                )
                cost_tracker.add_cost(entry)
            
            return result
        
        EnhancedAgentRunner.run_agent_multi_llm = tracked_run
        logger.info("Cost tracking integrated with agent runner")

# Start integration on module load
integrate_cost_tracking()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)