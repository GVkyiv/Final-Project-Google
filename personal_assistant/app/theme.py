from __future__ import annotations

import os
from dataclasses import dataclass

import customtkinter as ctk


@dataclass(frozen=True)
class UiTokens:
    outer_pad: int
    section_gap: int
    control_gap: int
    corner_radius: int
    card_corner_radius: int
    accent_color: tuple[str, str]


def get_ui_tokens(density: str = "normal") -> UiTokens:
    if density == "compact":
        return UiTokens(
            outer_pad=12,
            section_gap=10,
            control_gap=8,
            corner_radius=6,
            card_corner_radius=12,
            accent_color=("#6366F1", "#6366F1"),
        )
    return UiTokens(
        outer_pad=20,
        section_gap=16,
        control_gap=10,
        corner_radius=8,
        card_corner_radius=16,
        accent_color=("#6366F1", "#6366F1"),
    )


def apply_theme(root, density: str = "normal", appearance_mode: str = "system") -> UiTokens:
    mode = appearance_mode if appearance_mode in {"light", "dark", "system"} else "system"
    ctk.set_appearance_mode(mode)

    theme_path = os.path.join(os.path.dirname(__file__), "theme.json")
    if os.path.exists(theme_path):
        ctk.set_default_color_theme(theme_path)
    else:
        ctk.set_default_color_theme("blue")

    if density == "compact":
        ctk.set_widget_scaling(0.95)
        ctk.set_window_scaling(0.95)
    else:
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

    root.option_add("*tearOff", False)
    return get_ui_tokens(density)
