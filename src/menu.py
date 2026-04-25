from __future__ import annotations

import random
from typing import Callable, Optional

import arcade
import arcade.gui
from arcade.gui.widgets.buttons import UIFlatButtonStyle
from arcade.gui.widgets.text import UIInputTextStyle


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Multiplayer Games CMC 2026"

MENU_ACTIONS = [
    ("servers", "ДОСТУПНЫЕ СЕРВЕРЫ"),
    ("games", "ИГРЫ"),
    ("create_lobby", "СОЗДАТЬ ЛОББИ"),
    ("connect_lobby", "ПОДКЛЮЧИТЬСЯ К ЛОББИ"),
    ("exit", "ВЫХОД"),
]

CYAN = (58, 226, 255)
PURPLE = (174, 92, 255)
BG_TOP = (7, 10, 20)
BG_BOTTOM = (9, 24, 50)


def build_menu_button_style(exit_button: bool = False) -> dict:
    accent = PURPLE if exit_button else CYAN
    accent_hover = (203, 143, 255) if exit_button else (115, 233, 255)
    bg_normal = (20, 14, 42, 205) if exit_button else (8, 18, 44, 205)
    bg_hover = (40, 20, 70, 235) if exit_button else (13, 34, 78, 235)
    bg_press = (58, 26, 92, 255) if exit_button else (24, 50, 98, 255)
    return {
        "normal": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(232, 241, 255),
            bg=bg_normal,
            border=accent,
            border_width=2,
        ),
        "hover": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(241, 248, 255),
            bg=bg_hover,
            border=accent_hover,
            border_width=3,
        ),
        "press": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(255, 255, 255),
            bg=bg_press,
            border=accent_hover,
            border_width=3,
        ),
        "disabled": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(165, 176, 198),
            bg=(38, 42, 58, 180),
            border=(84, 96, 122),
            border_width=1,
        ),
    }


def build_primary_button_style() -> dict:
    return {
        "normal": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(240, 248, 255),
            bg=(10, 30, 70, 220),
            border=CYAN,
            border_width=2,
        ),
        "hover": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(255, 255, 255),
            bg=(15, 42, 88, 245),
            border=(120, 235, 255),
            border_width=3,
        ),
        "press": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(255, 255, 255),
            bg=(32, 58, 112, 255),
            border=(142, 241, 255),
            border_width=3,
        ),
        "disabled": UIFlatButtonStyle(
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=24,
            font_color=(165, 176, 198),
            bg=(38, 42, 58, 180),
            border=(84, 96, 122),
            border_width=1,
        ),
    }


def build_input_style() -> dict:
    return {
        "normal": UIInputTextStyle(bg=(8, 16, 42, 220), border=CYAN, border_width=2),
        "hover": UIInputTextStyle(bg=(10, 20, 56, 230), border=(122, 234, 255), border_width=2),
        "press": UIInputTextStyle(bg=(12, 25, 63, 240), border=(144, 241, 255), border_width=2),
        "disabled": UIInputTextStyle(bg=(34, 38, 56, 200), border=(102, 116, 142), border_width=2),
        "invalid": UIInputTextStyle(bg=(72, 19, 47, 210), border=(250, 118, 184), border_width=2),
    }


class NeonBaseView(arcade.View):
    """Базовый экран с неоновым sci-fi фоном."""

    def __init__(self):
        super().__init__()
        self.ui = arcade.gui.UIManager()
        self._stars = self._generate_stars(count=140)

    def on_show_view(self) -> None:
        self.ui.enable()

    def on_hide_view(self) -> None:
        self.ui.disable()

    def on_key_press(self, key: int, _modifiers: int) -> None:
        if key == arcade.key.ESCAPE:
            arcade.exit()

    def _add_centered_widget(self, widget, align_y: float = 0) -> None:
        anchor_widget_cls = getattr(arcade.gui, "UIAnchorWidget", None)
        if anchor_widget_cls is not None:
            self.ui.add(
                anchor_widget_cls(
                    anchor_x="center_x",
                    anchor_y="center_y",
                    align_y=align_y,
                    child=widget,
                )
            )
            return

        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(
            child=widget,
            anchor_x="center_x",
            anchor_y="center_y",
            align_y=align_y,
        )
        self.ui.add(anchor_layout)

    def _draw_neon_background(self) -> None:
        self._draw_vertical_gradient(top_color=BG_TOP, bottom_color=BG_BOTTOM, steps=60)
        self._draw_stars()
        self._draw_grid_perspective()
        self._draw_center_backlight()

    def _draw_vertical_gradient(
        self,
        top_color: tuple[int, int, int],
        bottom_color: tuple[int, int, int],
        steps: int = 32,
    ) -> None:
        width = self.window.width
        height = self.window.height
        step_h = max(height / steps, 1)

        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = self._lerp_rgb(top_color, bottom_color, t)
            bottom = i * step_h
            top = min((i + 1) * step_h, height)
            self._draw_filled_rect(0, width, bottom, top, color)

    @staticmethod
    def _lerp_rgb(
        color_a: tuple[int, int, int],
        color_b: tuple[int, int, int],
        t: float,
    ) -> tuple[int, int, int]:
        return (
            int(color_a[0] + (color_b[0] - color_a[0]) * t),
            int(color_a[1] + (color_b[1] - color_a[1]) * t),
            int(color_a[2] + (color_b[2] - color_a[2]) * t),
        )

    def _draw_stars(self) -> None:
        width = self.window.width
        height = self.window.height
        for x_ratio, y_ratio, radius, alpha in self._stars:
            x = x_ratio * width
            y = y_ratio * height
            arcade.draw_circle_filled(x, y, radius, (105, 182, 255, alpha))

    def _draw_grid_perspective(self) -> None:
        width = self.window.width
        height = self.window.height
        horizon_y = height * 0.20
        center_x = width * 0.50

        for i in range(-10, 11):
            x_bottom = center_x + i * (width / 16)
            x_top = center_x + i * 34
            arcade.draw_line(x_bottom, 0, x_top, horizon_y, (38, 123, 210, 40), line_width=1)

        rows = 16
        for i in range(rows):
            t = i / max(rows - 1, 1)
            y = horizon_y + (t * t) * (height * 0.45)
            alpha = int(16 + 42 * (1 - t))
            arcade.draw_line(0, y, width, y, (57, 135, 223, alpha), line_width=1)

    def _draw_center_backlight(self) -> None:
        width = self.window.width
        height = self.window.height
        self._draw_filled_rect(
            width * 0.28,
            width * 0.72,
            height * 0.80,
            height * 0.92,
            (22, 58, 120, 70),
        )
        self._draw_outlined_rect(
            width * 0.29,
            width * 0.71,
            height * 0.805,
            height * 0.915,
            (94, 206, 255, 110),
            border_width=2,
        )

    def _draw_filled_rect(self, left: float, right: float, bottom: float, top: float, color) -> None:
        if hasattr(arcade, "draw_lrbt_rectangle_filled"):
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
            return

        if hasattr(arcade, "draw_lrtb_rectangle_filled"):
            arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, color)
            return

        if hasattr(arcade, "draw_lbwh_rectangle_filled"):
            arcade.draw_lbwh_rectangle_filled(left, bottom, right - left, top - bottom, color)

    def _draw_outlined_rect(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        color,
        border_width: float = 1,
    ) -> None:
        if hasattr(arcade, "draw_lrbt_rectangle_outline"):
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, color, border_width)
            return

        if hasattr(arcade, "draw_lrtb_rectangle_outline"):
            arcade.draw_lrtb_rectangle_outline(left, right, top, bottom, color, border_width)
            return

        if hasattr(arcade, "draw_lbwh_rectangle_outline"):
            arcade.draw_lbwh_rectangle_outline(left, bottom, right - left, top - bottom, color, border_width)

    @staticmethod
    def _generate_stars(count: int) -> list[tuple[float, float, float, int]]:
        rng = random.Random(2026)
        stars: list[tuple[float, float, float, int]] = []
        for _ in range(count):
            x = rng.random()
            y = rng.uniform(0.24, 0.98)
            radius = rng.uniform(0.6, 1.8)
            alpha = rng.randint(45, 145)
            stars.append((x, y, radius, alpha))
        return stars


class VerticalCenteredInputText(arcade.gui.UIInputText):
    """UIInputText с центрированием текста по высоте внутри поля."""
    TEXT_LEFT_PADDING = 14
    LAYOUT_OFFSET = TEXT_LEFT_PADDING

    def _update_layout(self):
        super()._update_layout()
        # For IncrementalTextLayout in arcade 3.3.3 text is top-aligned at y=0.
        # To center it vertically, we must shift it down with a negative offset.
        vertical_gap = self.content_height - self.layout.content_height
        self.layout.y = int(-max(vertical_gap, 0) / 2)
        self.caret.on_layout_update()

    def on_click(self, event: arcade.gui.UIOnClickEvent):
        super().on_click(event)
        # Ensure caret becomes visible on every click, even if already active.
        self.caret.on_activate()
        self.trigger_full_render()


class RegistrationView(NeonBaseView):
    """Экран регистрации перед входом в меню."""

    def __init__(self):
        super().__init__()
        self.error_text = ""
        self.title_label = arcade.Text(
            "ДОБРО ПОЖАЛОВАТЬ",
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=52,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.prompt_label = arcade.Text(
            "ВВЕДИТЕ ИМЯ",
            x=0,
            y=0,
            color=(128, 219, 255),
            font_size=28,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.hint_label = arcade.Text(
            "Нажмите Enter или кнопку ПРОДОЛЖИТЬ",
            x=0,
            y=0,
            color=(165, 188, 214),
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
        )
        self.error_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(255, 142, 195),
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
        )

        self._build_ui()

    def _build_ui(self) -> None:
        form_box = arcade.gui.UIBoxLayout(space_between=16)

        self.name_input = VerticalCenteredInputText(
            width=560,
            height=64,
            text="",
            font_name=("Bahnschrift", "Calibri", "Arial"),
            font_size=26,
            text_color=(236, 247, 255),
            caret_color=CYAN,
            border_color=CYAN,
            border_width=2,
            style=build_input_style(),
        )

        @self.name_input.event("on_change")
        def on_change(_event):
            self.error_text = ""

        continue_button = arcade.gui.UIFlatButton(
            text="ПРОДОЛЖИТЬ",
            width=360,
            height=78,
            style=build_primary_button_style(),
        )

        @continue_button.event("on_click")
        def on_click(_event):
            self._submit_name()

        form_box.add(self.name_input)
        form_box.add(continue_button)
        self._add_centered_widget(form_box, align_y=-20)

    def on_show_view(self) -> None:
        super().on_show_view()
        if hasattr(self.ui, "_set_active_widget"):
            self.ui._set_active_widget(self.name_input)

    def on_draw(self) -> None:
        self.clear()
        self._draw_neon_background()
        self._draw_registration_shell()
        self._draw_text_layer()
        self.ui.draw()
        self._draw_input_focus_glow()

    def on_key_press(self, key: int, modifiers: int) -> None:
        if key in (arcade.key.ENTER, arcade.key.NUM_ENTER):
            self._submit_name()
            return
        super().on_key_press(key, modifiers)

    def _draw_registration_shell(self) -> None:
        width = self.window.width
        height = self.window.height
        self._draw_filled_rect(width * 0.20, width * 0.80, height * 0.18, height * 0.78, (5, 12, 30, 120))
        self._draw_outlined_rect(width * 0.20, width * 0.80, height * 0.18, height * 0.78, (66, 188, 255, 90), 2)
        self._draw_filled_rect(width * 0.25, width * 0.75, height * 0.60, height * 0.66, (20, 52, 110, 80))

    def _draw_text_layer(self) -> None:
        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.84
        self.title_label.draw()

        self.prompt_label.x = self.window.width / 2
        self.prompt_label.y = self.window.height * 0.63
        self.prompt_label.draw()

        self.hint_label.x = self.window.width / 2
        self.hint_label.y = self.window.height * 0.22
        self.hint_label.draw()

        self.error_label.text = self.error_text
        self.error_label.x = self.window.width / 2
        self.error_label.y = self.window.height * 0.28
        self.error_label.draw()

    def _draw_input_focus_glow(self) -> None:
        if not self.name_input.active:
            return

        pad_outer = 4
        pad_inner = 1
        self._draw_outlined_rect(
            self.name_input.left - pad_outer,
            self.name_input.right + pad_outer,
            self.name_input.bottom - pad_outer,
            self.name_input.top + pad_outer,
            (104, 228, 255, 220),
            border_width=2,
        )
        self._draw_outlined_rect(
            self.name_input.left - pad_inner,
            self.name_input.right + pad_inner,
            self.name_input.bottom - pad_inner,
            self.name_input.top + pad_inner,
            (157, 241, 255, 165),
            border_width=1,
        )

    def _submit_name(self) -> None:
        raw_name = self.name_input.text.strip()
        name = " ".join(raw_name.split())

        if not name:
            self.error_text = "Имя не может быть пустым."
            return

        if len(name) > 18:
            self.error_text = "Имя слишком длинное (максимум 18 символов)."
            return

        self.window.show_view(MainMenuView(player_name=name))


class MainMenuView(NeonBaseView):
    """Главный экран меню проекта."""

    def __init__(self, player_name: str, on_action: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.player_name = player_name
        self.on_action = on_action
        self.status_text = f"Игрок: {player_name}"

        self.title_label = arcade.Text(
            "ГЛАВНОЕ МЕНЮ",
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=52,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.status_label = arcade.Text(
            self.status_text,
            x=0,
            y=0,
            color=arcade.color.LIGHT_GRAY,
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
        )
        self.player_label = arcade.Text(
            player_name,
            x=0,
            y=0,
            color=(230, 241, 255),
            font_size=22,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.network_label = arcade.Text(
            "РЕГИОН: ЕВРОПА     42 MS",
            x=0,
            y=0,
            color=(154, 220, 255),
            font_size=20,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="left",
            anchor_y="center",
        )

        self._build_ui()

    def _build_ui(self) -> None:
        button_box = arcade.gui.UIBoxLayout(space_between=12)
        for action, title in MENU_ACTIONS:
            button = arcade.gui.UIFlatButton(
                text=title,
                width=620,
                height=82,
                style=build_menu_button_style(exit_button=(action == "exit")),
            )

            @button.event("on_click")
            def on_click(_event, menu_action=action, caption=title):
                self._handle_action(menu_action, caption)

            button_box.add(button)

        self._add_centered_widget(button_box, align_y=-30)

    def on_draw(self) -> None:
        self.clear()
        self._draw_neon_background()
        self._draw_menu_shell()
        self._draw_side_panels()
        self._draw_text_layer()
        self.ui.draw()

    def _draw_menu_shell(self) -> None:
        self._draw_filled_rect(
            self.window.width * 0.23,
            self.window.width * 0.77,
            self.window.height * 0.10,
            self.window.height * 0.78,
            (5, 12, 30, 95),
        )
        self._draw_outlined_rect(
            self.window.width * 0.23,
            self.window.width * 0.77,
            self.window.height * 0.10,
            self.window.height * 0.78,
            (66, 188, 255, 65),
            border_width=2,
        )

    def _draw_side_panels(self) -> None:
        width = self.window.width
        height = self.window.height

        left = 18
        right = 318
        bottom = height - 108
        top = height - 18
        self._draw_filled_rect(left, right, bottom, top, (5, 20, 46, 190))
        self._draw_outlined_rect(left, right, bottom, top, (57, 192, 255, 180), border_width=2)

        self.player_label.text = self.player_name
        self.player_label.x = (left + right) / 2
        self.player_label.y = (bottom + top) / 2
        self.player_label.draw()

        net_l = width - 372
        net_r = width - 18
        net_b = 18
        net_t = 74
        self._draw_filled_rect(net_l, net_r, net_b, net_t, (4, 18, 46, 205))
        self._draw_outlined_rect(net_l, net_r, net_b, net_t, (70, 202, 255, 175), border_width=2)
        self.network_label.x = net_l + 16
        self.network_label.y = (net_b + net_t) / 2
        self.network_label.draw()

    def _draw_text_layer(self) -> None:
        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.86
        self.title_label.draw()

        self.status_label.text = self.status_text
        self.status_label.x = self.window.width / 2
        self.status_label.y = self.window.height * 0.045
        self.status_label.draw()

    def _handle_action(self, action: str, caption: str) -> None:
        if action == "exit":
            arcade.exit()
            return

        self.status_text = f"{self.player_name}: выбрано '{caption}'"
        if self.on_action:
            self.on_action(action)


def run() -> None:
    window = arcade.Window(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        title=WINDOW_TITLE,
        resizable=True,
    )
    window.show_view(RegistrationView())
    arcade.run()


if __name__ == "__main__":
    run()
