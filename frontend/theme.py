"""Minimal Gradio theme for Clarke."""

import gradio as gr


def create_clarke_theme() -> gr.themes.base.Base:
    """Create the minimal fallback Gradio theme.

    Args:
        None: No parameters are required.

    Returns:
        gr.themes.base.Base: Basic theme object used only for compatibility.
    """

    return gr.themes.Base()


clarke_theme = create_clarke_theme()
