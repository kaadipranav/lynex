import functools
import time
from typing import Optional
from .client import WatchLLM

def monitor(name: Optional[str] = None):
    """
    Decorator to monitor function execution time, errors, and results.
    
    Usage:
    @monitor(name="my_function")
    def my_function():
        ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client = None
            try:
                client = WatchLLM.get_instance()
            except:
                # If SDK not initialized, just run the function
                return func(*args, **kwargs)

            start_time = time.time()
            func_name = name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Capture success span/log
                # For now, we'll just log it as a 'span' or 'log'
                client.capture_event("log", {
                    "message": f"Function {func_name} completed",
                    "level": "info",
                    "duration_ms": duration_ms
                }, context={"args": str(args), "kwargs": str(kwargs)})
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                client.capture_error(e, context={
                    "function": func_name,
                    "duration_ms": duration_ms,
                    "args": str(args),
                    "kwargs": str(kwargs)
                })
                raise
        return wrapper
    return decorator
