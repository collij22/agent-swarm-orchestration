#!/usr/bin/env python3
"""
Alert Manager
Monitors thresholds and triggers alerts for critical conditions
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from collections import defaultdict, deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Definition of an alert rule"""
    name: str
    description: str
    metric: str  # Metric to monitor
    condition: str  # Condition expression (e.g., "> 90")
    threshold: float
    severity: AlertSeverity
    duration_seconds: int = 0  # How long condition must persist
    cooldown_seconds: int = 300  # Cooldown between alerts
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """Evaluate if the condition is met"""
        if self.condition.startswith(">"):
            threshold = float(self.condition[1:].strip())
            return value > threshold
        elif self.condition.startswith(">="):
            threshold = float(self.condition[2:].strip())
            return value >= threshold
        elif self.condition.startswith("<"):
            threshold = float(self.condition[1:].strip())
            return value < threshold
        elif self.condition.startswith("<="):
            threshold = float(self.condition[2:].strip())
            return value <= threshold
        elif self.condition.startswith("=="):
            threshold = float(self.condition[2:].strip())
            return value == threshold
        elif self.condition.startswith("!="):
            threshold = float(self.condition[2:].strip())
            return value != threshold
        else:
            # Default to greater than
            return value > self.threshold


@dataclass
class Alert:
    """Active alert instance"""
    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    value: float
    threshold: float
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    notification_sent: bool = False
    
    @property
    def duration(self) -> timedelta:
        """Calculate alert duration"""
        end_time = self.resolved_at or datetime.now()
        return end_time - self.triggered_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "duration_seconds": self.duration.total_seconds(),
            "labels": self.labels,
            "annotations": self.annotations,
            "notification_sent": self.notification_sent
        }


class NotificationChannel:
    """Base class for notification channels"""
    
    async def send(self, alert: Alert) -> bool:
        """Send notification for alert"""
        raise NotImplementedError


class ConsoleNotification(NotificationChannel):
    """Console/terminal notification channel"""
    
    async def send(self, alert: Alert) -> bool:
        """Print alert to console"""
        icon = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.EMERGENCY: "🆘"
        }.get(alert.severity, "📢")
        
        print(f"\n{icon} ALERT: {alert.rule_name}")
        print(f"   Severity: {alert.severity.value.upper()}")
        print(f"   Message: {alert.message}")
        print(f"   Value: {alert.value:.2f} (threshold: {alert.threshold:.2f})")
        print(f"   Time: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True


class EmailNotification(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_host: str, smtp_port: int, 
                 from_email: str, to_emails: List[str],
                 username: str = None, password: str = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails
        self.username = username
        self.password = password
    
    async def send(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] Alert: {alert.rule_name}"
            
            body = f"""
Alert Triggered: {alert.rule_name}

Severity: {alert.severity.value.upper()}
Status: {alert.status.value}
Message: {alert.message}

Current Value: {alert.value:.2f}
Threshold: {alert.threshold:.2f}
Triggered At: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}

Labels: {json.dumps(alert.labels, indent=2)}
Annotations: {json.dumps(alert.annotations, indent=2)}

---
Agent Swarm Alert System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.username and self.password:
                    server.starttls()
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False


class FileNotification(NotificationChannel):
    """File-based notification channel"""
    
    def __init__(self, alerts_dir: str = "alerts"):
        self.alerts_dir = Path(alerts_dir)
        self.alerts_dir.mkdir(exist_ok=True)
    
    async def send(self, alert: Alert) -> bool:
        """Write alert to file"""
        alert_file = self.alerts_dir / f"alert_{alert.id}.json"
        
        with open(alert_file, 'w') as f:
            json.dump(alert.to_dict(), f, indent=2)
        
        return True


class AlertManager:
    """
    Manages alert rules, evaluations, and notifications
    """
    
    def __init__(self, production_monitor=None):
        """Initialize alert manager"""
        self.monitor = production_monitor
        
        # Alert rules
        self.rules: Dict[str, AlertRule] = {}
        self._setup_default_rules()
        
        # Active alerts
        self.active_alerts: Dict[str, Alert] = {}
        
        # Alert history
        self.alert_history: deque = deque(maxlen=1000)
        
        # Notification channels
        self.notification_channels: List[NotificationChannel] = [
            ConsoleNotification(),
            FileNotification()
        ]
        
        # Cooldown tracking
        self.rule_cooldowns: Dict[str, datetime] = {}
        
        # Pending alerts (for duration-based rules)
        self.pending_alerts: Dict[str, Dict] = {}
        
        # Alert counter
        self.alert_counter = 0
        
        # Suppression rules
        self.suppression_rules: List[Dict] = []
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        default_rules = [
            # Agent performance alerts
            AlertRule(
                name="high_agent_error_rate",
                description="Agent error rate exceeds threshold",
                metric="agent_error_rate",
                condition="> 0.2",
                threshold=0.2,
                severity=AlertSeverity.WARNING,
                duration_seconds=60,
                labels={"category": "performance", "component": "agent"}
            ),
            AlertRule(
                name="slow_agent_execution",
                description="Agent execution time exceeds threshold",
                metric="agent_duration_seconds",
                condition="> 120",
                threshold=120,
                severity=AlertSeverity.WARNING,
                duration_seconds=0,
                labels={"category": "performance", "component": "agent"}
            ),
            
            # System resource alerts
            AlertRule(
                name="high_memory_usage",
                description="System memory usage is critically high",
                metric="system_memory_percent",
                condition="> 85",
                threshold=85,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=30,
                labels={"category": "resources", "component": "system"}
            ),
            AlertRule(
                name="high_cpu_usage",
                description="System CPU usage is critically high",
                metric="system_cpu_percent",
                condition="> 90",
                threshold=90,
                severity=AlertSeverity.WARNING,
                duration_seconds=60,
                labels={"category": "resources", "component": "system"}
            ),
            AlertRule(
                name="low_disk_space",
                description="Disk space is running low",
                metric="system_disk_percent",
                condition="> 90",
                threshold=90,
                severity=AlertSeverity.WARNING,
                duration_seconds=0,
                labels={"category": "resources", "component": "system"}
            ),
            
            # API rate limit alerts
            AlertRule(
                name="api_rate_limit_critical",
                description="API rate limit nearly exhausted",
                metric="api_rate_limit_remaining",
                condition="< 10",
                threshold=10,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=0,
                labels={"category": "api", "component": "rate_limit"}
            ),
            
            # Cost alerts
            AlertRule(
                name="high_hourly_cost",
                description="Hourly cost exceeds budget",
                metric="cost_per_hour",
                condition="> 10",
                threshold=10.0,
                severity=AlertSeverity.WARNING,
                duration_seconds=0,
                labels={"category": "cost", "component": "billing"}
            ),
            AlertRule(
                name="daily_cost_exceeded",
                description="Daily cost exceeds budget",
                metric="cost_daily",
                condition="> 100",
                threshold=100.0,
                severity=AlertSeverity.CRITICAL,
                duration_seconds=0,
                labels={"category": "cost", "component": "billing"}
            ),
            
            # Requirement coverage alerts
            AlertRule(
                name="low_requirement_coverage",
                description="Requirement coverage is below target",
                metric="requirement_coverage",
                condition="< 0.8",
                threshold=0.8,
                severity=AlertSeverity.INFO,
                duration_seconds=300,
                labels={"category": "requirements", "component": "coverage"}
            ),
            
            # Throughput alerts
            AlertRule(
                name="low_throughput",
                description="System throughput is below expected",
                metric="throughput_per_hour",
                condition="< 10",
                threshold=10,
                severity=AlertSeverity.INFO,
                duration_seconds=300,
                labels={"category": "performance", "component": "throughput"}
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.notification_channels.append(channel)
    
    def add_suppression_rule(self, pattern: Dict):
        """Add a suppression rule to prevent alert spam"""
        self.suppression_rules.append(pattern)
    
    async def evaluate_rules(self, metrics: Dict):
        """Evaluate all rules against current metrics"""
        triggered_alerts = []
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule_name in self.rule_cooldowns:
                if datetime.now() < self.rule_cooldowns[rule_name]:
                    continue
            
            # Get metric value
            metric_value = self._get_metric_value(metrics, rule.metric)
            if metric_value is None:
                continue
            
            # Evaluate condition
            if rule.evaluate(metric_value):
                # Check duration requirement
                if rule.duration_seconds > 0:
                    if rule_name not in self.pending_alerts:
                        self.pending_alerts[rule_name] = {
                            "first_seen": datetime.now(),
                            "value": metric_value
                        }
                    else:
                        duration = (datetime.now() - self.pending_alerts[rule_name]["first_seen"]).total_seconds()
                        if duration >= rule.duration_seconds:
                            # Trigger alert
                            alert = await self._trigger_alert(rule, metric_value)
                            if alert:
                                triggered_alerts.append(alert)
                            del self.pending_alerts[rule_name]
                else:
                    # Immediate alert
                    alert = await self._trigger_alert(rule, metric_value)
                    if alert:
                        triggered_alerts.append(alert)
            else:
                # Condition not met, clear pending if exists
                if rule_name in self.pending_alerts:
                    del self.pending_alerts[rule_name]
                
                # Check if we should resolve an active alert
                active_alert_id = f"{rule_name}_{self._get_alert_key(rule, metrics)}"
                if active_alert_id in self.active_alerts:
                    await self.resolve_alert(active_alert_id)
        
        return triggered_alerts
    
    async def _trigger_alert(self, rule: AlertRule, value: float) -> Optional[Alert]:
        """Trigger an alert for a rule"""
        # Check if already active
        alert_key = self._get_alert_key(rule, {"value": value})
        alert_id = f"{rule.name}_{alert_key}"
        
        if alert_id in self.active_alerts:
            return None  # Already active
        
        # Check suppression
        if self._is_suppressed(rule, value):
            return None
        
        # Create alert
        self.alert_counter += 1
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            value=value,
            threshold=rule.threshold,
            message=f"{rule.description}: {value:.2f} {rule.condition} (threshold)",
            triggered_at=datetime.now(),
            labels=rule.labels,
            annotations=rule.annotations
        )
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Set cooldown
        self.rule_cooldowns[rule.name] = datetime.now() + timedelta(seconds=rule.cooldown_seconds)
        
        return alert
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]
        
        # Send resolution notification
        print(f"✅ Alert resolved: {alert.rule_name}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system"):
        """Acknowledge an active alert"""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by
        
        print(f"👍 Alert acknowledged: {alert.rule_name} by {acknowledged_by}")
        return True
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications through all channels"""
        for channel in self.notification_channels:
            try:
                success = await channel.send(alert)
                if success:
                    alert.notification_sent = True
            except Exception as e:
                print(f"Failed to send notification via {channel.__class__.__name__}: {e}")
    
    def _get_metric_value(self, metrics: Dict, metric_name: str) -> Optional[float]:
        """Extract metric value from metrics dictionary"""
        # This is a simplified version - in production, you'd have more sophisticated metric extraction
        if "." in metric_name:
            keys = metric_name.split(".")
            value = metrics
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return float(value) if value is not None else None
        else:
            return metrics.get(metric_name)
    
    def _get_alert_key(self, rule: AlertRule, metrics: Dict) -> str:
        """Generate unique key for alert deduplication"""
        # Simple implementation - could be enhanced with label-based keys
        return f"{datetime.now().strftime('%Y%m%d')}"
    
    def _is_suppressed(self, rule: AlertRule, value: float) -> bool:
        """Check if alert should be suppressed"""
        for suppression in self.suppression_rules:
            # Check if rule matches suppression pattern
            if suppression.get("rule_name") == rule.name:
                if "time_range" in suppression:
                    # Check time-based suppression
                    now = datetime.now()
                    start_time = datetime.strptime(suppression["time_range"]["start"], "%H:%M").time()
                    end_time = datetime.strptime(suppression["time_range"]["end"], "%H:%M").time()
                    if start_time <= now.time() <= end_time:
                        return True
                
                if "value_range" in suppression:
                    # Check value-based suppression
                    min_val = suppression["value_range"].get("min", float('-inf'))
                    max_val = suppression["value_range"].get("max", float('inf'))
                    if min_val <= value <= max_val:
                        return True
        
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alert status"""
        active_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_severity[alert.severity.value] += 1
        
        return {
            "total_active": len(self.active_alerts),
            "by_severity": dict(active_by_severity),
            "total_triggered_today": self.alert_counter,
            "pending_evaluations": len(self.pending_alerts),
            "active_alerts": [a.to_dict() for a in self.get_active_alerts()[:10]]
        }
    
    def export_rules(self, filepath: str):
        """Export alert rules to file"""
        rules_data = {
            rule_name: {
                "name": rule.name,
                "description": rule.description,
                "metric": rule.metric,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "duration_seconds": rule.duration_seconds,
                "cooldown_seconds": rule.cooldown_seconds,
                "labels": rule.labels,
                "annotations": rule.annotations,
                "enabled": rule.enabled
            }
            for rule_name, rule in self.rules.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(rules_data, f, indent=2)
    
    def import_rules(self, filepath: str):
        """Import alert rules from file"""
        with open(filepath, 'r') as f:
            rules_data = json.load(f)
        
        for rule_name, rule_data in rules_data.items():
            rule = AlertRule(
                name=rule_data["name"],
                description=rule_data["description"],
                metric=rule_data["metric"],
                condition=rule_data["condition"],
                threshold=rule_data["threshold"],
                severity=AlertSeverity(rule_data["severity"]),
                duration_seconds=rule_data.get("duration_seconds", 0),
                cooldown_seconds=rule_data.get("cooldown_seconds", 300),
                labels=rule_data.get("labels", {}),
                annotations=rule_data.get("annotations", {}),
                enabled=rule_data.get("enabled", True)
            )
            self.add_rule(rule)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_alerts():
        # Create alert manager
        manager = AlertManager()
        
        # Add email notification (example - configure with real SMTP)
        # email_channel = EmailNotification(
        #     smtp_host="smtp.gmail.com",
        #     smtp_port=587,
        #     from_email="alerts@example.com",
        #     to_emails=["admin@example.com"],
        #     username="alerts@example.com",
        #     password="password"
        # )
        # manager.add_notification_channel(email_channel)
        
        # Simulate metrics
        test_metrics = {
            "agent_error_rate": 0.25,  # Will trigger warning
            "system_memory_percent": 87,  # Will trigger critical
            "api_rate_limit_remaining": 5,  # Will trigger critical
            "cost_per_hour": 12.5  # Will trigger warning
        }
        
        print("Testing alert system...")
        
        # Evaluate rules
        alerts = await manager.evaluate_rules(test_metrics)
        
        print(f"\n{len(alerts)} alerts triggered")
        
        # Get summary
        summary = manager.get_alert_summary()
        print(f"\nAlert Summary:")
        print(json.dumps(summary, indent=2))
        
        # Acknowledge an alert
        if manager.active_alerts:
            first_alert_id = list(manager.active_alerts.keys())[0]
            manager.acknowledge_alert(first_alert_id, "test_user")
        
        # Export rules
        manager.export_rules("alert_rules.json")
        print("\nAlert rules exported to alert_rules.json")
    
    # Run test
    asyncio.run(test_alerts())