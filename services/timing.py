import time
from functools import wraps
import logging
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_timing_enabled():
    """Check whether timing logs are enabled"""
    return config.ENABLE_TIMING_LOGS

class Timer:
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not is_timing_enabled():
            return
            
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000  # Convert to milliseconds
        logger.info(f"⏱️  {self.name}: {duration:.2f}ms")

def timing_decorator(name):
    """Decorator for timing functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_timing_enabled():
                return func(*args, **kwargs)
                
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            logger.info(f"⏱️  {name}: {duration:.2f}ms")
            return result
        return wrapper
    return decorator

class RequestTimer:
    def __init__(self, request_id=None):
        self.request_id = request_id or str(int(time.time() * 1000))
        self.start_time = time.time()
        self.checkpoints = []
        self.enabled = is_timing_enabled()
        
    def checkpoint(self, name):
        if not self.enabled:
            return
            
        current_time = time.time()
        duration = (current_time - self.start_time) * 1000
        self.checkpoints.append((name, duration))
        logger.info(f"🔍 [{self.request_id}] {name}: {duration:.2f}ms")
        
    def summary(self):
        if not self.enabled:
            return
            
        total_time = (time.time() - self.start_time) * 1000
        logger.info(f"📊 [{self.request_id}] Total request time: {total_time:.2f}ms")
        logger.info(f"📋 [{self.request_id}] Breakdown:")
        for name, duration in self.checkpoints:
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            logger.info(f"   - {name}: {duration:.2f}ms ({percentage:.1f}%)")

# Runtime on/off switch
class TimingControl:
    @staticmethod
    def enable():
        """Enable timing logs at runtime"""
        config.ENABLE_TIMING_LOGS = True
        logger.info("🟢 Timing logs enabled")
    
    @staticmethod
    def disable():
        """Disable timing logs at runtime"""
        config.ENABLE_TIMING_LOGS = False
        logger.info("🔴 Timing logs disabled")
    
    @staticmethod
    def toggle():
        """Toggle timing log state"""
        if config.ENABLE_TIMING_LOGS:
            TimingControl.disable()
        else:
            TimingControl.enable()
    
    @staticmethod
    def status():
        """Get the current state"""
        status = "enabled" if config.ENABLE_TIMING_LOGS else "disabled"
        logger.info(f"📊 Timing logs are currently {status}")
        return config.ENABLE_TIMING_LOGS 