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
            body_background_fill="#F8F6F1",
            body_text_color="#1A1A2E",
            block_background_fill="#FFFFFF",
            block_border_color="#E8E4DC",
            block_label_text_color="#1A1A2E",
            block_title_text_color="#1B3A5C",
            button_primary_background_fill="#1B3A5C",
            button_primary_background_fill_hover="#2E6BAD",
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="#C9A84C",
            button_secondary_background_fill_hover="#E8D48B",
            button_secondary_text_color="#1B3A5C",
            color_accent="#C9A84C",
            color_accent_soft="#F5E6A3",
            link_text_color="#1B3A5C",
            link_text_color_hover="#2E6BAD",
            input_background_fill="#FFFFFF",
            input_border_color="#E8E4DC",
            input_border_color_focus="#2E6BAD",
        )
    )


clarke_theme = create_clarke_theme()
