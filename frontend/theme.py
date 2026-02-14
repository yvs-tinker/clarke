"""Clarke Gradio theme definitions."""

import gradio as gr


CLARKE_BLUE = gr.themes.Color(
    name="clarke_blue",
    c50="#EEF0F8",
    c100="#E0E8F5",
    c200="#C7D8EE",
    c300="#9FC0E4",
    c400="#78A8DA",
    c500="#4A90D9",
    c600="#2E6BAD",
    c700="#1B3A5C",
    c800="#16314E",
    c900="#112741",
    c950="#0D1E33",
)

CLARKE_GOLD = gr.themes.Color(
    name="clarke_gold",
    c50="#FFF9EA",
    c100="#FDF3D8",
    c200="#F5E6A3",
    c300="#EFD98F",
    c400="#E8D48B",
    c500="#C9A84C",
    c600="#AE8F3E",
    c700="#8B712F",
    c800="#6E5925",
    c900="#56461D",
    c950="#3F3316",
)

CLARKE_WARM_NEUTRAL = gr.themes.Color(
    name="clarke_warm_neutral",
    c50="#FFFEFC",
    c100="#F8F6F1",
    c200="#F1ECE3",
    c300="#E8E4DC",
    c400="#DCD4C8",
    c500="#C7BEB1",
    c600="#A99F94",
    c700="#8A8179",
    c800="#6E6760",
    c900="#56514B",
    c950="#3C3834",
)


def create_clarke_theme() -> gr.themes.base.Base:
    """Create the Clarke Gradio theme using PRD colour tokens.

    Args:
        None

    Returns:
        gr.themes.base.Base: Configured Gradio theme instance.
    """

    return (
        gr.themes.Base(
            primary_hue=CLARKE_BLUE,
            secondary_hue=CLARKE_GOLD,
            neutral_hue=CLARKE_WARM_NEUTRAL,
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
            button_primary_background_fill="linear-gradient(135deg, #1B3A5C 0%, #2E6BAD 100%)",
            button_primary_background_fill_hover="linear-gradient(135deg, #16314E 0%, #1B3A5C 100%)",
            button_primary_border_color="#1B3A5C",
            button_primary_text_color="#FFFFFF",
            button_secondary_background_fill="linear-gradient(135deg, #C9A84C 0%, #E8D48B 100%)",
            button_secondary_background_fill_hover="linear-gradient(135deg, #AE8F3E 0%, #C9A84C 100%)",
            button_secondary_border_color="#C9A84C",
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
