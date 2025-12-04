"""
Redis Stream Consumer for Event Processing.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError, ResponseError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from handlers import process_event

logger = logging.getLogger("lynex.processor.consumer")


# =============================================================================
# Constants
# =============================================================================

EVENTS_STREAM = "lynex:events:incoming"
CONSUMER_GROUP = "lynex-processors"
CONSUMER_NAME = f"processor-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

# How many events to fetch per batch
BATCH_SIZE = 10

# How long to block waiting for new events (ms)
BLOCK_TIMEOUT = 5000

# How long before claiming stuck messages (ms)
CLAIM_TIMEOUT = 60000


# =============================================================================
# Event Consumer Class
# =============================================================================

class EventConsumer:
    """
    Consumes events from Redis Stream using consumer groups.
    
    Consumer groups ensure:
    - Each event is processed by only one worker
    - Failed events can be retried
    - Multiple workers can scale horizontally
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.consumer_name = CONSUMER_NAME
        self.processed_count = 0
        self.error_count = 0
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True
    )
    async def initialize(self):
        """Initialize Redis connection and consumer group."""
        logger.info(f"Connecting to Redis: {settings.redis_url[:30]}...")
        
        self.client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
        )
        
        # Test connection
        await self.client.ping()
        logger.info("✅ Redis connection established")
        
        # Create consumer group (if not exists)
        try:
            await self.client.xgroup_create(
                EVENTS_STREAM,
                CONSUMER_GROUP,
                id="0",  # Start from beginning
                mkstream=True,  # Create stream if not exists
            )
            logger.info(f"✅ Consumer group '{CONSUMER_GROUP}' created")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{CONSUMER_GROUP}' already exists")
            else:
                raise
        except Exception as e:
             # If Redis is not ready, we want to retry
             logger.warning(f"Failed to create consumer group: {e}")
             raise e
        
        logger.info(f"Consumer name: {self.consumer_name}")
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def consume_loop(self, shutdown_event: asyncio.Event):
        """
        Main consumption loop.
        Reads events from the stream and processes them.
        """
        logger.info("Starting consumption loop...")
        
        while not shutdown_event.is_set():
            try:
                # Read new events from the stream
                events = await self.client.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=self.consumer_name,
                    streams={EVENTS_STREAM: ">"},  # ">" means only new messages
                    count=BATCH_SIZE,
                    block=BLOCK_TIMEOUT,
                )
                
                if events:
                    # events is a list of [stream_name, [(msg_id, data), ...]]
                    for stream_name, messages in events:
                        for msg_id, data in messages:
                            await self._process_message(msg_id, data)
                
                # Also check for stuck/pending messages periodically
                await self._claim_stuck_messages()
                
            except asyncio.CancelledError:
                logger.info("Consumption loop cancelled")
                break
            except (ConnectionError, TimeoutError) as e:
                logger.error(f"Redis connection error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Error in consumption loop: {e}", exc_info=True)
                await asyncio.sleep(1)
        
        logger.info(f"Consumption loop ended. Processed: {self.processed_count}, Errors: {self.error_count}")
    
    async def _process_message(self, msg_id: str, data: Dict[str, Any]):
        """Process a single message from the stream."""
        event_id = data.get("event_id", "unknown")
        
        try:
            logger.debug(f"Processing event {event_id} (msg: {msg_id})")
            
            # Parse the event data
            event = {
                "event_id": data.get("event_id"),
                "project_id": data.get("project_id"),
                "type": data.get("type"),
                "timestamp": data.get("timestamp"),
                "sdk": {
                    "name": data.get("sdk_name"),
                    "version": data.get("sdk_version"),
                },
                "body": json.loads(data.get("body", "{}")),
                "context": json.loads(data.get("context", "{}")),
                "queued_at": data.get("queued_at"),
            }
            
            # Process the event (this is where the magic happens)
            await process_event(event)
            
            # Acknowledge the message (remove from pending)
            await self.client.xack(EVENTS_STREAM, CONSUMER_GROUP, msg_id)
            
            self.processed_count += 1
            logger.info(f"✅ Processed event {event_id} ({self.processed_count} total)")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Error processing event {event_id}: {e}", exc_info=True)
            # Don't ACK - message will be retried
    
    async def _claim_stuck_messages(self):
        """
        Claim messages that have been pending too long.
        This handles cases where a worker crashed mid-processing.
        """
        try:
            # Get pending messages older than CLAIM_TIMEOUT
            pending = await self.client.xpending_range(
                EVENTS_STREAM,
                CONSUMER_GROUP,
                min="-",
                max="+",
                count=10,
            )
            
            for entry in pending:
                msg_id = entry["message_id"]
                idle_time = entry["time_since_delivered"]
                
                if idle_time > CLAIM_TIMEOUT:
                    # Claim the message for this consumer
                    claimed = await self.client.xclaim(
                        EVENTS_STREAM,
                        CONSUMER_GROUP,
                        self.consumer_name,
                        min_idle_time=CLAIM_TIMEOUT,
                        message_ids=[msg_id],
                    )
                    
                    if claimed:
                        logger.warning(f"Claimed stuck message {msg_id} (idle: {idle_time}ms)")
                        for msg_id, data in claimed:
                            await self._process_message(msg_id, data)
                            
        except Exception as e:
            # Non-critical, just log and continue
            logger.debug(f"Error checking pending messages: {e}")
