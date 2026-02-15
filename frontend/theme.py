"""Gradio theme configuration for Clarke UI."""

import gradio as gr


def create_clarke_theme() -> gr.themes.base.Base:
    """Create the Clarke theme with explicit body/background overrides.

    Args:
        None: No parameters are required.

    Returns:
        gr.themes.base.Base: Configured theme object for the Clarke application.
    """

    return gr.themes.Base(
        primary_hue=gr.themes.Color(
            c50="#FFF9E6",
            c100="#FFF3CC",
            c200="#FFE799",
            c300="#FFDB66",
            c400="#F0D060",
            c500="#D4AF37",
            c600="#B8941F",
            c700="#9A7B1A",
            c800="#7C6215",
            c900="#5E4910",
            c950="#3F3010",
        ),
        font=gr.themes.GoogleFont("Inter"),
        font_mono=gr.themes.GoogleFont("JetBrains Mono"),
    ).set(
        body_background_fill="#F8F6F1",
        body_background_fill_dark="#F8F6F1",
        background_fill_primary="#F8F6F1",
        background_fill_secondary="transparent",
        block_background_fill="transparent",
        block_border_width="0px",
        block_shadow="none",
        layout_gap="0px",
        block_padding="0px",
    )


clarke_theme = create_clarke_theme()
