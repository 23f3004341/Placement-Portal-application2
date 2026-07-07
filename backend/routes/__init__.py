"""Compatibility import for the Flask API blueprint.

The active user interface is the Vue single-page application. All server-side
routes are JSON APIs defined in api_routes.py, apart from the SPA entry point
and service-worker asset.
"""

from .api_routes import main

__all__ = ["main"]
