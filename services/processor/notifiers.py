"""
Alert Notifiers - Send alerts via various channels.
"""

import logging
import asyncio
from typing import Optional
from dataclasses import dataclass
import httpx

from config import settings

logger = logging.getLogger("lynex.notifiers")


@dataclass
class NotificationResult:
    success: bool
    channel: str
    error: Optional[str] = None


class WebhookNotifier:
    """Send alerts to a webhook URL."""
    
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send(self, alert) -> NotificationResult:
        try:
            payload = {
                "type": "alert",
                "rule_id": alert.rule_id,
                "rule_name": alert.rule_name,
                "project_id": alert.project_id,
                "severity": alert.severity.value,
                "message": alert.message,
                "event_id": alert.event_id,
                "metadata": alert.metadata,
            }
            
            response = await self.client.post(self.url, json=payload)
            
            if response.status_code < 300:
                logger.info(f"✅ Webhook sent: {alert.rule_name}")
                return NotificationResult(success=True, channel="webhook")
            else:
                logger.error(f"❌ Webhook failed: {response.status_code}")
                return NotificationResult(success=False, channel="webhook", error=f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
            return NotificationResult(success=False, channel="webhook", error=str(e))
    
    async def close(self):
        await self.client.aclose()


class SlackNotifier:
    """Send alerts to Slack via incoming webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send(self, alert) -> NotificationResult:
        try:
            # Emoji based on severity
            emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "critical": "🚨",
            }.get(alert.severity.value, "📢")
            
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} {alert.rule_name}",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:* {alert.message}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Project:* {alert.project_id} | *Severity:* {alert.severity.value}"
                            }
                        ]
                    }
                ]
            }
            
            response = await self.client.post(self.webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Slack notification sent: {alert.rule_name}")
                return NotificationResult(success=True, channel="slack")
            else:
                return NotificationResult(success=False, channel="slack", error=f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Slack error: {e}")
            return NotificationResult(success=False, channel="slack", error=str(e))
    
    async def close(self):
        await self.client.aclose()


class ConsoleNotifier:
    """Print alerts to console (for development)."""
    
    async def send(self, alert) -> NotificationResult:
        severity_colors = {
            "info": "\033[94m",     # Blue
            "warning": "\033[93m",  # Yellow
            "critical": "\033[91m", # Red
        }
        reset = "\033[0m"
        color = severity_colors.get(alert.severity.value, "")
        
        print(f"\n{color}{'='*60}")
        print(f"🚨 ALERT: {alert.rule_name}")
        print(f"   Severity: {alert.severity.value.upper()}")
        print(f"   Message: {alert.message}")
        print(f"   Project: {alert.project_id}")
        print(f"   Event ID: {alert.event_id}")
        print(f"{'='*60}{reset}\n")
        
        return NotificationResult(success=True, channel="console")
    
    async def close(self):
        pass


# Global notifier instances
_notifiers = []


def init_notifiers():
    """Initialize notifiers based on config."""
    global _notifiers
    _notifiers = []
    
    # Always add console for dev
    _notifiers.append(ConsoleNotifier())
    
    # Add webhook if configured
    webhook_url = getattr(settings, 'alert_webhook_url', None)
    if webhook_url:
        _notifiers.append(WebhookNotifier(webhook_url))
    
    # Add Slack if configured
    slack_url = getattr(settings, 'slack_webhook_url', None)
    if slack_url:
        _notifiers.append(SlackNotifier(slack_url))
    
    logger.info(f"Initialized {len(_notifiers)} notifiers")


async def send_alert(alert):
    """Send alert through all configured notifiers."""
    if not _notifiers:
        init_notifiers()
    
    results = await asyncio.gather(
        *[notifier.send(alert) for notifier in _notifiers],
        return_exceptions=True
    )
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Notifier error: {result}")


async def close_notifiers():
    """Cleanup notifiers."""
    for notifier in _notifiers:
        await notifier.close()
