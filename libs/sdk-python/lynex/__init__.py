from .client import Lynex
from .decorators import monitor

def init(api_key: str, project_id: str, host: str = "http://localhost:8000"):
    return Lynex.init(api_key, project_id, host)

def capture_event(event_type: str, body: dict, context: dict = None):
    Lynex.get_instance().capture_event(event_type, body, context)

def capture_log(message: str, level: str = "info", context: dict = None):
    Lynex.get_instance().capture_log(message, level, context)

def capture_error(exception: Exception, context: dict = None):
    Lynex.get_instance().capture_error(exception, context)

def capture_llm_usage(model: str, input_tokens: int, output_tokens: int, cost: float = 0.0):
    Lynex.get_instance().capture_llm_usage(model, input_tokens, output_tokens, cost)

