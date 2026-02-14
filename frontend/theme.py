"""Clarke Gradio theme definitions."""

import gradio as gr


def create_clarke_theme() -> gr.themes.base.Base:
    """Create the Clarke Gradio theme using PRD colour tokens.

    Args:
        None

    Returns:
        gr.themes.base.Base: Configured Gradio theme instance.
    """
    return (
        gr.themes.Base(
            primary_hue="blue",
            secondary_hue="amber",
            neutral_hue="slate",
            radius_size="lg",
            spacing_size="md",
        )
        .set(
            body_background_fill="#FAFBFD",
            body_text_color="#1A1A2E",
            block_background_fill="#FFFFFF",
            block_border_color="#E2E6EE",
            block_label_text_color="#1A1A2E",
            block_title_text_color="#1A1A2E",
            button_primary_background_fill="#1E3A5F",
            button_primary_background_fill_hover="#2B5EA7",
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="#D4A035",
            button_secondary_background_fill_hover="#F0D078",
            button_secondary_text_color="#1A1A2E",
            color_accent="#D4A035",
            color_accent_soft="#F0D078",
            link_text_color="#1E3A5F",
            link_text_color_hover="#2B5EA7",
            input_background_fill="#FFFFFF",
            input_border_color="#E2E6EE",
            input_border_color_focus="#1E3A5F",
        )
    )


clarke_theme = create_clarke_theme()
