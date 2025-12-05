import os
import time
import uuid
import logging
import threading
import queue
import atexit
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger("watchllm")

class WatchLLM:
    _instance = None

    def __init__(self, api_key: str, project_id: str, host: str = "http://localhost:8000"):
        self.api_key = api_key
        self.project_id = project_id
        self.host = host.rstrip("/")
        self.queue = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        
        # Register cleanup
        atexit.register(self.shutdown)
        WatchLLM._instance = self

    @classmethod
    def init(cls, api_key: str, project_id: str, host: str = "http://localhost:8000"):
        """Initialize the global WatchLLM client."""
        if cls._instance:
            logger.warning("WatchLLM already initialized")
            return cls._instance
        return cls(api_key, project_id, host)

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            raise RuntimeError("WatchLLM not initialized. Call WatchLLM.init() first.")
        return cls._instance

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    def _send_event_with_retry(self, session: requests.Session, url: str, event: Dict[str, Any]) -> requests.Response:
        """Send event with retry logic."""
        response = session.post(url, json=event, timeout=5)
        response.raise_for_status()  # Raise on 4xx/5xx
        return response

    def _worker(self):
        """Background worker to send events."""
        session = requests.Session()
        session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })
        
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                # Get event with timeout to allow checking stop_event
                try:
                    event = self.queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Send event with retry
                try:
                    url = f"{self.host}/api/v1/events"
                    response = self._send_event_with_retry(session, url, event)
                    if response.status_code == 202:
                        logger.debug(f"Event sent successfully: {event.get('eventId')}")
                    else:
                        logger.warning(f"Unexpected response: {response.status_code}")
                except Exception as e:
                    logger.error(f"Failed to send event after retries: {e}")
                finally:
                    self.queue.task_done()
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def capture_event(self, event_type: str, body: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        """Queue an event to be sent."""
        if self._stop_event.is_set():
            return

        event = {
            "eventId": str(uuid.uuid4()),
            "projectId": self.project_id,
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "sdk": {
                "name": "watchllm-python",
                "version": "0.1.0"
            },
            "body": body,
            "context": context or {}
        }

        try:
            self.queue.put_nowait(event)
        except queue.Full:
            logger.warning("WatchLLM event queue full, dropping event")

    def capture_log(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
        self.capture_event("log", {"message": message, "level": level}, context)

    def capture_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        import traceback
        body = {
            "type": type(exception).__name__,
            "message": str(exception),
            "stacktrace": traceback.format_exc()
        }
        self.capture_event("error", body, context)

    def capture_llm_usage(self, model: str, input_tokens: int, output_tokens: int, cost: float = 0.0):
        body = {
            "model": model,
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "totalTokens": input_tokens + output_tokens,
            "cost": cost
        }
        self.capture_event("token_usage", body)

    def shutdown(self):
        """Flush queue and stop worker."""
        if self._stop_event.is_set():
            return
            
        logger.info("WatchLLM shutting down, flushing events...")
        self._stop_event.set()
        
        # Wait for queue to empty (with timeout)
        if not self.queue.empty():
            try:
                # Give it 5 seconds to flush (account for retries)
                self._worker_thread.join(timeout=5.0)
            except:
                pass
