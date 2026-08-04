# this module handles sending notifications to the user, if it's configured
from __future__ import annotations

import logging
import os

import requests
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


class NotificationClient:
    def __init__(self, url: str | None = None, token: str | None = None, *, enabled: bool = False) -> None:
        self.url = url
        self.token = token
        self.enabled = enabled

    @classmethod
    def from_env(cls, enabled: bool = False) -> NotificationClient:
        # merge process env with a local .env file (env takes precedence)
        values: dict[str, str | None] = {**dotenv_values(), **os.environ}

        def get(key: str) -> str | None:
            value = values.get(key)
            return value or None

        return cls(url=get("NTFY_URL"), token=get("NTFY_TOKEN"), enabled=enabled)

    @property
    def configured(self) -> bool:
        return bool(self.url)

    def notify(self, message: str) -> None:
        if not self.enabled or not self.url:
            return
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else None
        try:
            response = requests.post(self.url, data=message.encode(encoding="utf-8"), headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as error:
            logger.warning("Failed to send notification: %s", error)
            return
        logger.info("Notification sent: %s", message)
