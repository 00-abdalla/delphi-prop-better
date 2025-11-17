"""Rate limiting utilities for API calls."""
import time
from functools import wraps
from typing import Callable

from backend.app.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 18):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls allowed per minute
        """
        self.min_delay = 60.0 / calls_per_minute  # Seconds between calls
        self.last_call_time = 0.0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_delay:
            sleep_time = self.min_delay - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()


def rate_limited(calls_per_minute: int = 18):
    """
    Decorator to rate limit function calls.
    
    Args:
        calls_per_minute: Maximum calls allowed per minute
        
    Returns:
        Decorated function that respects rate limit
    """
    limiter = RateLimiter(calls_per_minute)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
        return wrapper
    return decorator
