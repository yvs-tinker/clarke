"""Application entry point mounting Clarke Gradio UI within FastAPI."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
import gradio as gr

from backend.api import app as fast_api
from backend.config import get_settings
from frontend.ui import build_ui


def create_app() -> FastAPI:
    """Create the FastAPI application with mounted Gradio interface.

    Args:
        None: Uses existing FastAPI API app and Gradio UI builder.

    Returns:
        FastAPI: Unified ASGI app serving API and web UI.
    """

    demo = build_ui()
    return gr.mount_gradio_app(fast_api, demo, path="/")


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
