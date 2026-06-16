"""Entry point.

Kept as a thin re-export so the service stays importable as ``app:app`` (the
Dockerfile CMD and the tests depend on it). All implementation lives in the
``twin`` package.
"""

from twin.api import app

__all__ = ["app"]
