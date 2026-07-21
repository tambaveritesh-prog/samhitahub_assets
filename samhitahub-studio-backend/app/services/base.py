"""
Base service class.

`BaseService` is intentionally minimal today — it just standardizes how
services obtain a logger. As shared cross-service behavior emerges
(e.g. metrics/timing decorators, retry helpers), add it here so every
service benefits automatically.
"""

from __future__ import annotations

import logging


class BaseService:
    """Parent class for all application services."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__module__)

    @property
    def logger(self) -> logging.Logger:
        return self._logger
