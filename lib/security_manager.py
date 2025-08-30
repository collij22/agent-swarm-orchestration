#!/usr/bin/env python3
"""
Security Manager - Production security hardening for agent swarm system

Features:
- API key rotation with secure storage
- Per-user/project rate limiting
- Input sanitization and validation
- Comprehensive audit logging
- Role-Based Access Control (RBAC)
"""

import os
import json
import time
import hashlib
import secrets
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, deque

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False
    print("Warning: PyJWT not installed. Install with: pip install pyjwt")

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("Warning: cryptography not installed. Install with: pip install cryptography")


class AccessLevel(Enum):
    """Access levels for RBAC"""
    ADMIN = "admin"          # Full system access
    DEVELOPER = "developer"  # Execute workflows, view logs
    VIEWER = "viewer"        # Read-only access
    GUEST = "guest"          # Limited trial access


class SecurityEvent(Enum):
    """Security event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    API_KEY_ROTATION = "api_key_rotation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class User:
    """User entity for RBAC"""
    user_id: str
    username: str
    email: str
    role: AccessLevel
    api_keys: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """Audit log entry"""
    timestamp: datetime
    event_type: SecurityEvent
    user_id: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    action: str
    success: bool
    details: Dict[str, Any]
    risk_score: int = 0  # 0-100 risk score


class APIKeyManager:
    """Manages API key rotation and secure storage"""
    
    def __init__(self, rotation_interval_days: int = 30):
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.keys_dir = Path("./secure/api_keys")
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption if available
        self.cipher = None
        if HAS_CRYPTO:
            self.encryption_key = self._get_or_create_encryption_key()
            self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = self.keys_dir / ".master.key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            # Set restrictive permissions on key file
            if os.name != 'nt':  # Unix-like systems
                os.chmod(key_file, 0o600)
            return key
    
    def generate_api_key(self, user_id: str, project: str = "default") -> str:
        """Generate a new API key for a user/project"""
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)
        
        # Create key metadata
        key_data = {
            "user_id": user_id,
            "project": project,
            "key": raw_key,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + self.rotation_interval).isoformat(),
            "is_active": True
        }
        
        # Store encrypted key data
        self._store_key(user_id, project, key_data)
        
        # Return formatted key
        return f"sk-{project}-{raw_key}"
    
    def _store_key(self, user_id: str, project: str, key_data: Dict):
        """Store API key data securely"""
        key_file = self.keys_dir / f"{user_id}_{project}.json"
        
        if self.cipher:
            # Encrypt the key data
            encrypted = self.cipher.encrypt(json.dumps(key_data).encode())
            key_file.write_bytes(encrypted)
        else:
            # Fallback to plain JSON (not recommended for production)
            key_file.write_text(json.dumps(key_data, indent=2))
    
    def validate_key(self, api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate an API key and return (valid, user_id, project)"""
        # Parse key format
        if not api_key.startswith("sk-"):
            return False, None, None
        
        try:
            _, project, raw_key = api_key.split("-", 2)
        except ValueError:
            return False, None, None
        
        # Check all stored keys
        for key_file in self.keys_dir.glob("*.json"):
            if key_file.name.startswith("."):
                continue
                
            key_data = self._load_key(key_file)
            if not key_data:
                continue
            
            if (key_data.get("project") == project and 
                key_data.get("key") == raw_key and
                key_data.get("is_active")):
                
                # Check expiration
                expires_at = datetime.fromisoformat(key_data["expires_at"])
                if datetime.now() > expires_at:
                    return False, None, None
                
                return True, key_data["user_id"], project
        
        return False, None, None
    
    def _load_key(self, key_file: Path) -> Optional[Dict]:
        """Load and decrypt key data"""
        try:
            if self.cipher:
                encrypted = key_file.read_bytes()
                decrypted = self.cipher.decrypt(encrypted)
                return json.loads(decrypted)
            else:
                return json.loads(key_file.read_text())
        except Exception:
            return None
    
    def rotate_key(self, user_id: str, project: str = "default") -> str:
        """Rotate API key for a user/project"""
        # Deactivate old key
        old_key_file = self.keys_dir / f"{user_id}_{project}.json"
        if old_key_file.exists():
            key_data = self._load_key(old_key_file)
            if key_data:
                key_data["is_active"] = False
                key_data["rotated_at"] = datetime.now().isoformat()
                # Archive old key
                archive_file = self.keys_dir / f"archive_{user_id}_{project}_{int(time.time())}.json"
                self._store_key(f"archive_{user_id}", project, key_data)
        
        # Generate new key
        return self.generate_api_key(user_id, project)
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        valid, user_id, project = self.validate_key(api_key)
        if not valid:
            return False
        
        key_file = self.keys_dir / f"{user_id}_{project}.json"
        if key_file.exists():
            key_data = self._load_key(key_file)
            if key_data:
                key_data["is_active"] = False
                key_data["revoked_at"] = datetime.now().isoformat()
                self._store_key(user_id, project, key_data)
                return True
        
        return False


class RateLimiter:
    """Rate limiting per user/project with sliding window"""
    
    def __init__(self):
        self.limits = {
            AccessLevel.ADMIN: {"requests_per_minute": 100, "requests_per_hour": 2000},
            AccessLevel.DEVELOPER: {"requests_per_minute": 60, "requests_per_hour": 1000},
            AccessLevel.VIEWER: {"requests_per_minute": 30, "requests_per_hour": 500},
            AccessLevel.GUEST: {"requests_per_minute": 10, "requests_per_hour": 100}
        }
        
        # Sliding window for tracking requests
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=2000))
        # Try to get or create event loop for async lock
        try:
            loop = asyncio.get_running_loop()
            self.lock = asyncio.Lock()
        except RuntimeError:
            # No event loop running, will use synchronous locking
            self.lock = None
    
    async def check_rate_limit(self, user_id: str, role: AccessLevel, 
                               project: str = "default") -> Tuple[bool, Optional[int]]:
        """Check if request is within rate limits. Returns (allowed, retry_after_seconds)"""
        key = f"{user_id}:{project}"
        current_time = time.time()
        
        if self.lock:
            async with self.lock:
                return self._check_limit(key, role, current_time)
        else:
            return self._check_limit(key, role, current_time)
    
    def _check_limit(self, key: str, role: AccessLevel, current_time: float) -> Tuple[bool, Optional[int]]:
        """Internal rate limit check"""
        history = self.request_history[key]
        limits = self.limits[role]
        
        # Clean old entries (older than 1 hour)
        cutoff_time = current_time - 3600
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Check per-minute limit
        minute_ago = current_time - 60
        minute_requests = sum(1 for t in history if t > minute_ago)
        if minute_requests >= limits["requests_per_minute"]:
            retry_after = 60 - (current_time - history[-limits["requests_per_minute"]])
            return False, int(retry_after)
        
        # Check per-hour limit
        hour_requests = len(history)
        if hour_requests >= limits["requests_per_hour"]:
            retry_after = 3600 - (current_time - history[0])
            return False, int(retry_after)
        
        # Add current request
        history.append(current_time)
        return True, None
    
    def get_usage_stats(self, user_id: str, project: str = "default") -> Dict[str, Any]:
        """Get current usage statistics for a user/project"""
        key = f"{user_id}:{project}"
        current_time = time.time()
        history = self.request_history[key]
        
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        return {
            "requests_last_minute": sum(1 for t in history if t > minute_ago),
            "requests_last_hour": sum(1 for t in history if t > hour_ago),
            "oldest_request": datetime.fromtimestamp(history[0]).isoformat() if history else None,
            "newest_request": datetime.fromtimestamp(history[-1]).isoformat() if history else None
        }


class InputSanitizer:
    """Input sanitization and validation"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',                 # JavaScript protocol
        r'on\w+\s*=',                   # Event handlers
        r'\.\./',                       # Path traversal
        r';\s*DROP\s+TABLE',           # SQL injection
        r'--\s*$',                      # SQL comment
        r'UNION\s+SELECT',              # SQL injection
        r'exec\s*\(',                   # Command execution
        r'eval\s*\(',                   # Code evaluation
        r'__import__',                  # Python import
        r'subprocess',                  # Process execution
        r'os\.',                        # OS module access
    ]
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 10000) -> str:
        """Sanitize string input"""
        if not input_str:
            return ""
        
        # Truncate to max length
        input_str = input_str[:max_length]
        
        # Remove null bytes
        input_str = input_str.replace('\x00', '')
        
        # Check for dangerous patterns
        for pattern in InputSanitizer.DANGEROUS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                raise ValueError(f"Dangerous pattern detected: {pattern}")
        
        # Basic HTML entity encoding
        input_str = (input_str
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;'))
        
        return input_str
    
    @staticmethod
    def sanitize_path(path_str: str) -> str:
        """Sanitize file path input"""
        if not path_str:
            return ""
        
        # Remove null bytes
        path_str = path_str.replace('\x00', '')
        
        # Prevent path traversal
        if '..' in path_str or path_str.startswith('/'):
            raise ValueError("Path traversal attempt detected")
        
        # Normalize path
        path = Path(path_str)
        
        # Ensure path is relative and within bounds
        try:
            path.resolve().relative_to(Path.cwd())
        except ValueError:
            raise ValueError("Path outside working directory")
        
        return str(path)
    
    @staticmethod
    def validate_json(json_str: str) -> Dict:
        """Validate and parse JSON input"""
        try:
            data = json.loads(json_str)
            
            # Recursively sanitize strings in the JSON
            def sanitize_dict(obj):
                if isinstance(obj, dict):
                    return {k: sanitize_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize_dict(item) for item in obj]
                elif isinstance(obj, str):
                    return InputSanitizer.sanitize_string(obj, max_length=1000)
                else:
                    return obj
            
            return sanitize_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")


class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, log_dir: str = "./logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_file = None
        self.log_buffer = []
        self.buffer_size = 100
        self.risk_analyzer = RiskAnalyzer()
    
    def log_event(self, event_type: SecurityEvent, user_id: Optional[str] = None,
                  ip_address: Optional[str] = None, resource: Optional[str] = None,
                  action: str = "", success: bool = True, details: Dict[str, Any] = None):
        """Log a security event"""
        
        # Calculate risk score
        risk_score = self.risk_analyzer.calculate_risk(
            event_type, user_id, ip_address, success, details
        )
        
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            success=success,
            details=details or {},
            risk_score=risk_score
        )
        
        # Add to buffer
        self.log_buffer.append(entry)
        
        # Flush if buffer is full
        if len(self.log_buffer) >= self.buffer_size:
            self.flush()
        
        # Alert on high-risk events
        if risk_score > 70:
            self._alert_high_risk(entry)
    
    def flush(self):
        """Flush log buffer to file"""
        if not self.log_buffer:
            return
        
        # Rotate log file daily
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{today}.jsonl"
        
        with open(log_file, "a") as f:
            for entry in self.log_buffer:
                log_data = {
                    "timestamp": entry.timestamp.isoformat(),
                    "event_type": entry.event_type.value,
                    "user_id": entry.user_id,
                    "ip_address": entry.ip_address,
                    "resource": entry.resource,
                    "action": entry.action,
                    "success": entry.success,
                    "details": entry.details,
                    "risk_score": entry.risk_score
                }
                f.write(json.dumps(log_data) + "\n")
        
        self.log_buffer.clear()
    
    def _alert_high_risk(self, entry: AuditLogEntry):
        """Alert on high-risk security events"""
        alert_file = self.log_dir / "alerts.jsonl"
        alert_data = {
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type.value,
            "risk_score": entry.risk_score,
            "user_id": entry.user_id,
            "details": entry.details,
            "alert": "HIGH_RISK_EVENT"
        }
        
        with open(alert_file, "a") as f:
            f.write(json.dumps(alert_data) + "\n")
    
    def query_logs(self, start_date: datetime = None, end_date: datetime = None,
                   user_id: str = None, event_type: SecurityEvent = None,
                   min_risk_score: int = 0) -> List[Dict]:
        """Query audit logs with filters"""
        results = []
        
        # Determine date range
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        # Iterate through log files in date range
        current_date = start_date
        while current_date <= end_date:
            log_file = self.log_dir / f"audit_{current_date.strftime('%Y-%m-%d')}.jsonl"
            if log_file.exists():
                with open(log_file) as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)
                            
                            # Apply filters
                            if user_id and log_entry.get("user_id") != user_id:
                                continue
                            if event_type and log_entry.get("event_type") != event_type.value:
                                continue
                            if log_entry.get("risk_score", 0) < min_risk_score:
                                continue
                            
                            results.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            
            current_date += timedelta(days=1)
        
        return results


class RiskAnalyzer:
    """Analyze risk scores for security events"""
    
    def __init__(self):
        self.failed_login_attempts = defaultdict(int)
        self.suspicious_patterns = defaultdict(list)
    
    def calculate_risk(self, event_type: SecurityEvent, user_id: Optional[str],
                       ip_address: Optional[str], success: bool,
                       details: Dict[str, Any]) -> int:
        """Calculate risk score (0-100) for an event"""
        risk_score = 0
        
        # Base risk by event type
        risk_scores = {
            SecurityEvent.LOGIN_FAILURE: 20,
            SecurityEvent.UNAUTHORIZED_ACCESS: 60,
            SecurityEvent.RATE_LIMIT_EXCEEDED: 30,
            SecurityEvent.SUSPICIOUS_ACTIVITY: 80,
            SecurityEvent.CONFIGURATION_CHANGE: 40,
        }
        
        risk_score = risk_scores.get(event_type, 10)
        
        # Increase risk for repeated failures
        if event_type == SecurityEvent.LOGIN_FAILURE and user_id:
            self.failed_login_attempts[user_id] += 1
            if self.failed_login_attempts[user_id] > 3:
                risk_score += 20
            if self.failed_login_attempts[user_id] > 5:
                risk_score += 30
        
        # Reset counter on success
        if event_type == SecurityEvent.LOGIN_SUCCESS and user_id:
            self.failed_login_attempts[user_id] = 0
        
        # Check for suspicious patterns
        if ip_address:
            recent_events = self.suspicious_patterns[ip_address]
            recent_events.append(time.time())
            
            # Keep only last hour
            cutoff = time.time() - 3600
            recent_events = [t for t in recent_events if t > cutoff]
            self.suspicious_patterns[ip_address] = recent_events
            
            # Many events from same IP
            if len(recent_events) > 50:
                risk_score += 20
        
        # Cap at 100
        return min(risk_score, 100)


class RBACManager:
    """Role-Based Access Control manager"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.permissions = {
            AccessLevel.ADMIN: [
                "workflow.execute", "workflow.create", "workflow.delete",
                "agent.execute", "agent.create", "agent.delete",
                "logs.read", "logs.delete", "config.read", "config.write",
                "user.create", "user.delete", "user.modify"
            ],
            AccessLevel.DEVELOPER: [
                "workflow.execute", "workflow.create",
                "agent.execute", "logs.read", "config.read"
            ],
            AccessLevel.VIEWER: [
                "workflow.read", "agent.read", "logs.read"
            ],
            AccessLevel.GUEST: [
                "workflow.read"
            ]
        }
    
    def create_user(self, username: str, email: str, role: AccessLevel) -> User:
        """Create a new user"""
        user_id = hashlib.sha256(f"{username}:{email}".encode()).hexdigest()[:16]
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role
        )
        self.users[user_id] = user
        return user
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        user_permissions = self.permissions.get(user.role, [])
        
        # Check exact permission or wildcard
        for perm in user_permissions:
            if perm == permission or perm.endswith("*"):
                base = perm[:-1]
                if permission.startswith(base):
                    return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        user = self.users.get(user_id)
        if not user:
            return []
        return self.permissions.get(user.role, [])


class SecurityManager:
    """Main security manager integrating all components"""
    
    def __init__(self):
        self.api_key_manager = APIKeyManager()
        self.rate_limiter = RateLimiter()
        self.input_sanitizer = InputSanitizer()
        self.audit_logger = AuditLogger()
        self.rbac_manager = RBACManager()
        
        # Session management
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(hours=24)
    
    async def authenticate(self, api_key: str, ip_address: str = None) -> Tuple[bool, Optional[str]]:
        """Authenticate a request with API key"""
        # Validate API key
        valid, user_id, project = self.api_key_manager.validate_key(api_key)
        
        if not valid:
            self.audit_logger.log_event(
                SecurityEvent.LOGIN_FAILURE,
                ip_address=ip_address,
                action="Invalid API key",
                success=False,
                details={"api_key_prefix": api_key[:10] if api_key else None}
            )
            return False, None
        
        # Check if user exists and is active
        user = self.rbac_manager.users.get(user_id)
        if not user or not user.is_active:
            self.audit_logger.log_event(
                SecurityEvent.UNAUTHORIZED_ACCESS,
                user_id=user_id,
                ip_address=ip_address,
                action="Inactive user",
                success=False
            )
            return False, None
        
        # Check rate limit
        allowed, retry_after = await self.rate_limiter.check_rate_limit(
            user_id, user.role, project
        )
        
        if not allowed:
            self.audit_logger.log_event(
                SecurityEvent.RATE_LIMIT_EXCEEDED,
                user_id=user_id,
                ip_address=ip_address,
                action="Rate limit exceeded",
                success=False,
                details={"retry_after": retry_after}
            )
            return False, None
        
        # Success
        self.audit_logger.log_event(
            SecurityEvent.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            action="API authentication",
            success=True
        )
        
        # Update last login
        user.last_login = datetime.now()
        
        return True, user_id
    
    def authorize(self, user_id: str, resource: str, action: str) -> bool:
        """Authorize a user action on a resource"""
        permission = f"{resource}.{action}"
        authorized = self.rbac_manager.check_permission(user_id, permission)
        
        if not authorized:
            self.audit_logger.log_event(
                SecurityEvent.UNAUTHORIZED_ACCESS,
                user_id=user_id,
                resource=resource,
                action=action,
                success=False,
                details={"permission": permission}
            )
        else:
            self.audit_logger.log_event(
                SecurityEvent.DATA_ACCESS,
                user_id=user_id,
                resource=resource,
                action=action,
                success=True
            )
        
        return authorized
    
    def sanitize_input(self, input_data: Any, input_type: str = "string") -> Any:
        """Sanitize user input based on type"""
        if input_type == "string":
            return self.input_sanitizer.sanitize_string(str(input_data))
        elif input_type == "path":
            return self.input_sanitizer.sanitize_path(str(input_data))
        elif input_type == "json":
            return self.input_sanitizer.validate_json(input_data)
        else:
            return input_data
    
    def rotate_api_keys(self):
        """Rotate all API keys (scheduled task)"""
        rotated_count = 0
        
        for user_id, user in self.rbac_manager.users.items():
            for project in user.metadata.get("projects", ["default"]):
                try:
                    new_key = self.api_key_manager.rotate_key(user_id, project)
                    rotated_count += 1
                    
                    self.audit_logger.log_event(
                        SecurityEvent.API_KEY_ROTATION,
                        user_id=user_id,
                        action="Scheduled rotation",
                        success=True,
                        details={"project": project}
                    )
                except Exception as e:
                    self.audit_logger.log_event(
                        SecurityEvent.API_KEY_ROTATION,
                        user_id=user_id,
                        action="Rotation failed",
                        success=False,
                        details={"error": str(e)}
                    )
        
        return rotated_count
    
    def get_security_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate security report for the last N days"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Query audit logs
        logs = self.audit_logger.query_logs(start_date=start_date)
        
        # Analyze logs
        report = {
            "period": f"Last {days} days",
            "total_events": len(logs),
            "failed_logins": sum(1 for log in logs if log.get("event_type") == SecurityEvent.LOGIN_FAILURE.value),
            "rate_limits_hit": sum(1 for log in logs if log.get("event_type") == SecurityEvent.RATE_LIMIT_EXCEEDED.value),
            "unauthorized_attempts": sum(1 for log in logs if log.get("event_type") == SecurityEvent.UNAUTHORIZED_ACCESS.value),
            "high_risk_events": sum(1 for log in logs if log.get("risk_score", 0) > 70),
            "unique_users": len(set(log.get("user_id") for log in logs if log.get("user_id"))),
            "unique_ips": len(set(log.get("ip_address") for log in logs if log.get("ip_address")))
        }
        
        # Top risks
        high_risk_events = [log for log in logs if log.get("risk_score", 0) > 70]
        report["top_risks"] = high_risk_events[:10]
        
        return report


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Initialize security manager
        security = SecurityManager()
        
        # Create users
        admin = security.rbac_manager.create_user("admin", "admin@example.com", AccessLevel.ADMIN)
        dev = security.rbac_manager.create_user("developer", "dev@example.com", AccessLevel.DEVELOPER)
        
        # Generate API keys
        admin_key = security.api_key_manager.generate_api_key(admin.user_id)
        dev_key = security.api_key_manager.generate_api_key(dev.user_id)
        
        print(f"Admin API Key: {admin_key}")
        print(f"Developer API Key: {dev_key}")
        
        # Test authentication
        auth_result, user_id = await security.authenticate(admin_key, "127.0.0.1")
        print(f"Authentication result: {auth_result}, User: {user_id}")
        
        # Test authorization
        can_delete = security.authorize(admin.user_id, "workflow", "delete")
        print(f"Admin can delete workflow: {can_delete}")
        
        can_delete_dev = security.authorize(dev.user_id, "workflow", "delete")
        print(f"Developer can delete workflow: {can_delete_dev}")
        
        # Test input sanitization
        try:
            clean_input = security.sanitize_input("<script>alert('xss')</script>", "string")
            print(f"Sanitized input: {clean_input}")
        except ValueError as e:
            print(f"Sanitization error: {e}")
        
        # Test rate limiting
        for i in range(15):
            allowed, retry = await security.rate_limiter.check_rate_limit(
                dev.user_id, dev.role
            )
            if not allowed:
                print(f"Rate limited at request {i+1}, retry after {retry}s")
                break
        
        # Generate security report
        report = security.get_security_report(days=1)
        print(f"Security Report: {json.dumps(report, indent=2)}")
        
        # Flush audit logs
        security.audit_logger.flush()
    
    # Run demo
    asyncio.run(demo())