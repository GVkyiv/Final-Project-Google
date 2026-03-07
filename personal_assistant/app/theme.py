from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk


@dataclass(frozen=True)
class UiTokens:
    outer_pad: int
    section_gap: int
    control_gap: int
    corner_radius: int


def get_ui_tokens(density: str = "normal") -> UiTokens:
    if density == "compact":
        return UiTokens(outer_pad=10, section_gap=8, control_gap=6, corner_radius=10)
    return UiTokens(outer_pad=14, section_gap=12, control_gap=8, corner_radius=12)


def apply_theme(root, density: str = "normal", appearance_mode: str = "system") -> UiTokens:
    mode = appearance_mode if appearance_mode in {"light", "dark", "system"} else "system"
    ctk.set_appearance_mode(mode)
    ctk.set_default_color_theme("blue")

    if density == "compact":
        ctk.set_widget_scaling(0.95)
        ctk.set_window_scaling(0.95)
    else:
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

    root.option_add("*tearOff", False)
    return get_ui_tokens(density)
