"""
Retry manager for handling errors and retries in AI automation.

This module provides robust error handling and retry logic for AI operations,
including exponential backoff and detailed error logging.
"""

import time
import logging
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from enum import Enum


class RetryReason(Enum):
    """Enumeration of retry reasons."""
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    PLATFORM_ERROR = "platform_error"
    UNKNOWN_ERROR = "unknown_error"


class RetryManager:
    """
    Manager for handling retries and error recovery in AI automation.
    
    This class provides sophisticated retry logic with exponential backoff,
    error categorization, and detailed logging.
    """
    
    def __init__(self, logger: logging.Logger, max_retries: int = 5):
        """
        Initialize the retry manager.
        
        Args:
            logger: Logger instance for logging operations
            max_retries: Maximum number of retries per operation
        """
        self.logger = logger
        self.max_retries = max_retries
        self.retry_history: List[Dict[str, Any]] = []
        
        # Retry delays for different error types (in seconds)
        self.retry_delays = {
            RetryReason.NETWORK_ERROR: [2, 5, 10, 20, 40],
            RetryReason.TIMEOUT: [5, 10, 15, 30, 60],
            RetryReason.ELEMENT_NOT_FOUND: [1, 2, 4, 8, 16],
            RetryReason.PERMISSION_DENIED: [0, 0, 0, 0, 0],  # No point in retrying
            RetryReason.RATE_LIMITED: [10, 30, 60, 120, 300],
            RetryReason.PLATFORM_ERROR: [3, 6, 12, 24, 48],
            RetryReason.UNKNOWN_ERROR: [2, 4, 8, 16, 32]
        }
    
    def categorize_error(self, error: Exception) -> RetryReason:
        """
        Categorize an error to determine retry strategy.
        
        Args:
            error: The exception that occurred
            
        Returns:
            RetryReason: The category of the error
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in [
            'connection', 'network', 'dns', 'socket', 'ssl', 'certificate'
        ]):
            return RetryReason.NETWORK_ERROR
        
        # Timeout errors
        if any(keyword in error_str for keyword in [
            'timeout', 'timed out', 'time out'
        ]):
            return RetryReason.TIMEOUT
        
        # Element not found errors (Selenium)
        if any(keyword in error_str for keyword in [
            'no such element', 'element not found', 'unable to locate'
        ]):
            return RetryReason.ELEMENT_NOT_FOUND
        
        # Permission errors
        if any(keyword in error_str for keyword in [
            'permission denied', 'unauthorized', 'forbidden', 'access denied'
        ]):
            return RetryReason.PERMISSION_DENIED
        
        # Rate limiting errors
        if any(keyword in error_str for keyword in [
            'rate limit', 'too many requests', 'quota exceeded'
        ]):
            return RetryReason.RATE_LIMITED
        
        # Platform-specific errors
        if any(keyword in error_str for keyword in [
            'openai', 'chatgpt', 'claude', 'gemini', 'ai error'
        ]):
            return RetryReason.PLATFORM_ERROR
        
        return RetryReason.UNKNOWN_ERROR
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            bool: True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        
        reason = self.categorize_error(error)
        
        # Some errors should not be retried
        if reason == RetryReason.PERMISSION_DENIED:
            return False
        
        return True
    
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """
        Get the delay before retrying an operation.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            float: Delay in seconds
        """
        reason = self.categorize_error(error)
        delays = self.retry_delays.get(reason, self.retry_delays[RetryReason.UNKNOWN_ERROR])
        
        if attempt < len(delays):
            return delays[attempt]
        else:
            # For attempts beyond our predefined delays, use exponential backoff
            return min(delays[-1] * (2 ** (attempt - len(delays) + 1)), 300)  # Max 5 minutes
    
    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Any, Optional[str]]:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: The operation to execute
            operation_name: Name of the operation for logging
            context: Additional context information
            
        Returns:
            Tuple of (success, result, error_message)
        """
        attempt = 0
        last_error = None
        error_messages = []
        
        while attempt <= self.max_retries:
            try:
                self.logger.info(f"Executing {operation_name} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                result = operation()
                
                if attempt > 0:
                    self.logger.info(f"{operation_name} succeeded after {attempt + 1} attempts")
                
                # Log successful retry
                self.retry_history.append({
                    "operation": operation_name,
                    "context": context,
                    "attempts": attempt + 1,
                    "success": True,
                    "timestamp": time.time()
                })
                
                return True, result, None
                
            except Exception as error:
                last_error = error
                error_msg = f"Attempt {attempt + 1} failed: {str(error)}"
                error_messages.append(error_msg)
                self.logger.warning(error_msg)
                
                if not self.should_retry(error, attempt):
                    break
                
                # Calculate and wait for retry delay
                delay = self.get_retry_delay(error, attempt)
                if delay > 0:
                    self.logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                
                attempt += 1
        
        # All retries exhausted
        final_error_msg = f"{operation_name} failed after {attempt + 1} attempts. Errors: {'; '.join(error_messages)}"
        self.logger.error(final_error_msg)
        
        # Log failed retry
        self.retry_history.append({
            "operation": operation_name,
            "context": context,
            "attempts": attempt + 1,
            "success": False,
            "error": str(last_error),
            "error_type": self.categorize_error(last_error).value,
            "timestamp": time.time()
        })
        
        return False, None, final_error_msg
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about retry operations.
        
        Returns:
            Dict[str, Any]: Statistics about retries
        """
        if not self.retry_history:
            return {"total_operations": 0}
        
        total_ops = len(self.retry_history)
        successful_ops = sum(1 for op in self.retry_history if op["success"])
        failed_ops = total_ops - successful_ops
        
        total_attempts = sum(op["attempts"] for op in self.retry_history)
        avg_attempts = total_attempts / total_ops if total_ops > 0 else 0
        
        # Error type distribution
        error_types = {}
        for op in self.retry_history:
            if not op["success"] and "error_type" in op:
                error_type = op["error_type"]
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "total_attempts": total_attempts,
            "average_attempts_per_operation": avg_attempts,
            "error_type_distribution": error_types
        }
    
    def clear_history(self):
        """Clear retry history."""
        self.retry_history.clear()
        self.logger.info("Retry history cleared")


def retry_on_failure(
    max_retries: int = 5,
    logger: Optional[logging.Logger] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_retries: Maximum number of retries
        logger: Logger instance (optional)
        operation_name: Name for logging (optional, uses function name)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger, operation_name
            
            if logger is None:
                logger = logging.getLogger(__name__)
            
            if operation_name is None:
                operation_name = func.__name__
            
            retry_manager = RetryManager(logger, max_retries)
            
            def operation():
                return func(*args, **kwargs)
            
            success, result, error_msg = retry_manager.execute_with_retry(
                operation, operation_name
            )
            
            if success:
                return result
            else:
                raise Exception(error_msg)
        
        return wrapper
    return decorator


# Example usage decorators for common operations
def retry_selenium_operation(max_retries: int = 3):
    """Decorator for Selenium operations with appropriate retry settings."""
    return retry_on_failure(max_retries=max_retries, operation_name="selenium_operation")


def retry_ai_operation(max_retries: int = 5):
    """Decorator for AI operations with appropriate retry settings."""
    return retry_on_failure(max_retries=max_retries, operation_name="ai_operation")


def retry_network_operation(max_retries: int = 3):
    """Decorator for network operations with appropriate retry settings."""
    return retry_on_failure(max_retries=max_retries, operation_name="network_operation")