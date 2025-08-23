"""
Compatibility wrapper to expose the FastAPI `app` as `app.main.app`.

Several tests import `from app.main import app`. The primary application
entrypoint lives at project root in `main.py`. This module re-exports the
same FastAPI instance to satisfy those imports without duplicating logic.
"""

from main import app  # re-export

__all__ = ["app"]


