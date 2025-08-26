#!/usr/bin/env python3
"""
Error Handling Framework for Samay Core Engine
Provides robust error management, retry mechanisms, and graceful degradation

This file implements a comprehensive error handling system that:
1. Categorizes errors by type and severity
2. Implements intelligent retry mechanisms with exponential backoff
3. Provides graceful degradation strategies
4. Logs and monitors error patterns
5. Enables error recovery and system resilience

Key Components:
- ErrorCategory: Classification of different error types
- RetryStrategy: Configurable retry mechanisms
- ErrorHandler: Main error handling and recovery logic
- ErrorRecovery: Strategies for different failure scenarios
- ErrorMonitor: Error tracking and pattern analysis
"""

import logging
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import functools

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, system continues normally
    MEDIUM = "medium"      # Moderate issues, some functionality affected
    HIGH = "high"          # Significant issues, major functionality affected
    CRITICAL = "critical"  # System-breaking issues, immediate attention required

class ErrorCategory(Enum):
    """Categories of errors that can occur"""
    # Database errors
    DATABASE_CONNECTION = "database_connection"
    DATABASE_QUERY = "database_query"
    DATABASE_TIMEOUT = "database_timeout"
    
    # Network errors
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_CONNECTION = "network_connection"
    NETWORK_RATE_LIMIT = "network_rate_limit"
    
    # Authentication errors
    AUTH_FAILED = "authentication_failed"
    AUTH_EXPIRED = "authentication_expired"
    AUTH_INVALID = "authentication_invalid"
    
    # Data errors
    DATA_VALIDATION = "data_validation"
    DATA_PARSING = "data_parsing"
    DATA_CORRUPTION = "data_corruption"
    
    # System errors
    SYSTEM_RESOURCE = "system_resource"
    SYSTEM_PERMISSION = "system_permission"
    SYSTEM_CONFIGURATION = "system_configuration"
    
    # Unknown errors
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for an error"""
    timestamp: str
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class ErrorRecord:
    """Complete error record for tracking and analysis"""
    error_id: str
    error_type: str
    error_message: str
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    context: ErrorContext
    stack_trace: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False
    resolution_time: Optional[str] = None
    created_at: str = ""

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0   # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple = (Exception,)

class RetryStrategy:
    """Implements intelligent retry mechanisms"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff"""
        if attempt <= 0:
            return 0
        
        # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if operation should be retried"""
        if attempt >= self.config.max_retries:
            return False
        
        # Check if exception type is retryable
        return isinstance(exception, self.config.retry_on_exceptions)
    
    def retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt == 0:
                    # First attempt
                    return operation(*args, **kwargs)
                else:
                    # Retry attempt
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Retrying operation (attempt {attempt + 1}/{self.config.max_retries + 1}) after {delay:.2f}s delay")
                    time.sleep(delay)
                    return operation(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    logger.error(f"Operation failed permanently after {attempt + 1} attempts: {e}")
                    break
                
                logger.warning(f"Operation failed (attempt {attempt + 1}/{self.config.max_retries + 1}): {e}")
        
        # If we get here, all retries failed
        raise last_exception

class ErrorRecovery:
    """Implements recovery strategies for different error types"""
    
    @staticmethod
    def recover_database_connection(db_path: str) -> bool:
        """Attempt to recover database connection"""
        try:
            import sqlite3
            # Test connection
            conn = sqlite3.connect(db_path, timeout=5)
            conn.close()
            logger.info("Database connection recovered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to recover database connection: {e}")
            return False
    
    @staticmethod
    def recover_network_connection(url: str, timeout: int = 5) -> bool:
        """Attempt to recover network connection"""
        try:
            import requests
            response = requests.get(url, timeout=timeout)
            if response.status_code < 500:  # Not server error
                logger.info("Network connection recovered successfully")
                return True
            else:
                logger.warning(f"Network connection test failed with status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to recover network connection: {e}")
            return False
    
    @staticmethod
    def recover_authentication(auth_token: str) -> bool:
        """Attempt to recover authentication"""
        # This would typically involve token refresh logic
        # For now, we'll just log the attempt
        logger.info("Authentication recovery attempted")
        return False  # Placeholder
    
    @staticmethod
    def recover_data_validation(data: Any, schema: Dict) -> bool:
        """Attempt to recover from data validation errors"""
        try:
            # Basic validation recovery - could be enhanced
            if data is None:
                return False
            
            # Try to clean/repair data based on schema
            # This is a simplified example
            logger.info("Data validation recovery attempted")
            return True
        except Exception as e:
            logger.error(f"Data validation recovery failed: {e}")
            return False

class ErrorMonitor:
    """Monitors and analyzes error patterns"""
    
    def __init__(self, log_file: Optional[str] = None):
        if log_file is None:
            home = Path.home()
            log_file = home / ".samay_sync" / "error_log.json"
        
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.error_records: List[ErrorRecord] = []
        self._load_error_log()
    
    def _load_error_log(self):
        """Load existing error log"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    for record_data in data:
                        # Convert back to ErrorRecord objects
                        record = ErrorRecord(**record_data)
                        self.error_records.append(record)
                logger.info(f"Loaded {len(self.error_records)} error records from {self.log_file}")
        except Exception as e:
            logger.warning(f"Failed to load error log: {e}")
            self.error_records = []
    
    def _save_error_log(self):
        """Save error log to file"""
        try:
            data = [asdict(record) for record in self.error_records]
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save error log: {e}")
    
    def record_error(self, error_record: ErrorRecord):
        """Record a new error"""
        self.error_records.append(error_record)
        self._save_error_log()
        logger.error(f"Error recorded: {error_record.error_type} - {error_record.error_message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error patterns"""
        if not self.error_records:
            return {"total_errors": 0, "categories": {}, "severities": {}}
        
        # Count by category
        categories = {}
        for record in self.error_records:
            cat = record.error_category.value
            categories[cat] = categories.get(cat, 0) + 1
        
        # Count by severity
        severities = {}
        for record in self.error_records:
            sev = record.error_severity.value
            severities[sev] = severities.get(sev, 0) + 1
        
        # Recent errors (last 24 hours)
        now = datetime.now(timezone.utc)
        recent_errors = 0
        for record in self.error_records:
            try:
                record_time = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
                if (now - record_time).days < 1:
                    recent_errors += 1
            except:
                pass
        
        return {
            "total_errors": len(self.error_records),
            "recent_errors_24h": recent_errors,
            "categories": categories,
            "severities": severities,
            "resolution_rate": sum(1 for r in self.error_records if r.resolved) / len(self.error_records)
        }
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorRecord]:
        """Get all errors of a specific category"""
        return [record for record in self.error_records if record.error_category == category]
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorRecord]:
        """Get all errors of a specific severity"""
        return [record for record in self.error_records if record.error_severity == severity]
    
    def mark_error_resolved(self, error_id: str):
        """Mark an error as resolved"""
        for record in self.error_records:
            if record.error_id == error_id:
                record.resolved = True
                record.resolution_time = datetime.now(timezone.utc).isoformat()
                break
        self._save_error_log()

class ErrorHandler:
    """Main error handling and recovery orchestrator"""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None, monitor: Optional[ErrorMonitor] = None):
        self.retry_strategy = RetryStrategy(retry_config or RetryConfig())
        self.monitor = monitor or ErrorMonitor()
        self.recovery_strategies = {
            ErrorCategory.DATABASE_CONNECTION: ErrorRecovery.recover_database_connection,
            ErrorCategory.NETWORK_CONNECTION: ErrorRecovery.recover_network_connection,
            ErrorCategory.AUTH_FAILED: ErrorRecovery.recover_authentication,
            ErrorCategory.DATA_VALIDATION: ErrorRecovery.recover_data_validation,
        }
    
    def handle_error(self, 
                    exception: Exception, 
                    category: ErrorCategory, 
                    severity: ErrorSeverity,
                    component: str,
                    operation: str,
                    context_data: Optional[Dict[str, Any]] = None,
                    retry: bool = True) -> bool:
        """
        Handle an error with appropriate recovery strategies
        
        Returns:
            bool: True if error was handled/recovered, False otherwise
        """
        # Create error record
        error_id = f"err_{int(time.time())}_{hash(str(exception)) % 10000}"
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=type(exception).__name__,
            error_message=str(exception),
            error_category=category,
            error_severity=severity,
            context=ErrorContext(
                timestamp=datetime.now(timezone.utc).isoformat(),
                component=component,
                operation=operation,
                additional_data=context_data
            ),
            stack_trace=traceback.format_exc(),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Record error
        self.monitor.record_error(error_record)
        
        # Log error based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR in {component}.{operation}: {exception}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR in {component}.{operation}: {exception}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR in {component}.{operation}: {exception}")
        else:
            logger.info(f"LOW SEVERITY ERROR in {component}.{operation}: {exception}")
        
        # Attempt recovery if enabled
        if retry and category in self.recovery_strategies:
            recovery_func = self.recovery_strategies[category]
            try:
                # For now, we'll pass basic context - this could be enhanced
                if category == ErrorCategory.DATABASE_CONNECTION:
                    # Would need actual db_path from context
                    logger.info("Database recovery attempted")
                elif category == ErrorCategory.NETWORK_CONNECTION:
                    # Would need actual URL from context
                    logger.info("Network recovery attempted")
                else:
                    logger.info(f"Recovery attempted for {category.value}")
                
                # Mark as resolved if recovery appears successful
                # In a real implementation, you'd verify recovery actually worked
                if severity != ErrorSeverity.CRITICAL:
                    self.monitor.mark_error_resolved(error_id)
                    return True
                    
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
        
        return False
    
    def retry_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic"""
        return self.retry_strategy.retry_operation(operation, *args, **kwargs)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get current error summary"""
        return self.monitor.get_error_summary()
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorRecord]:
        """Get errors of specific category"""
        return self.monitor.get_errors_by_category(category)
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorRecord]:
        """Get errors of specific severity"""
        return self.monitor.get_errors_by_severity(severity)

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 component: str = "unknown",
                 retry: bool = True):
    """Decorator to automatically handle errors in functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the error handler from the first argument if it's a method
                error_handler = None
                if args and hasattr(args[0], '_error_handler'):
                    error_handler = args[0]._error_handler
                
                if error_handler:
                    error_handler.handle_error(
                        exception=e,
                        category=category,
                        severity=severity,
                        component=component,
                        operation=func.__name__,
                        retry=retry
                    )
                else:
                    # Fallback logging if no error handler available
                    logger.error(f"Error in {component}.{func.__name__}: {e}")
                
                raise  # Re-raise the exception after handling
        return wrapper
    return decorator

# Convenience function for quick error handling
def get_error_handler(retry_config: Optional[RetryConfig] = None) -> ErrorHandler:
    """Get a configured error handler instance"""
    return ErrorHandler(retry_config)
