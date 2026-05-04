from __future__ import annotations

import asyncio
import random
import textwrap
from math import ceil
from pathlib import Path
from typing import Callable, Optional

import arcade
import arcade.gui
from arcade.gui.widgets.buttons import UIFlatButtonStyle
from arcade.gui.widgets.text import UIInputTextStyle

try:
    from .frontend import Menager
except ImportError:
    from frontend import Menager


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Multiplayer Games CMC 2026"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GAMES_MEDIA_DIR = PROJECT_ROOT / "media" / "games"

MENU_ACTIONS = [
    ("create_lobby", "СОЗДАТЬ ЛОББИ"),
    ("lobbies", "ДОСТУПНЫЕ ЛОББИ"),
    ("games", "ИГРЫ"),
    ("exit", "ВЫХОД"),
]

GAME_CARDS = [
    {
        "title": "Tanks 1990",
        "rules": "Два игрока управляют танками на арене. Цель: первым уничтожить соперника нужное число раз.",
        "colors": ((39, 94, 62), (87, 190, 122)),
        "image": "tanks_1990.jpg",
    },
    {
        "title": "Pong",
        "rules": "Классический пинг-понг: двигайте ракетку и отбивайте мяч. Очко получает тот, кто отправил мяч за край соперника.",
        "colors": ((26, 72, 116), (95, 186, 255)),
        "image": "pong.jpg",
    },
    {
        "title": "X and O",
        "rules": "Крестики-нолики для двух игроков. Побеждает тот, кто первым соберет линию из трех своих символов.",
        "colors": ((81, 46, 126), (184, 128, 255)),
        "image": "x_0.jpg",
    },
    {
        "title": "Морской бой",
        "rules": "Разместите флот на поле и по очереди стреляйте по клеткам противника. Побеждает уничтоживший все корабли.",
        "colors": ((36, 66, 121), (106, 161, 255)),
        "image": "sea_battle.jpg",
    },
    {
        "title": "Викторина",
        "rules": "Игроки отвечают на одинаковые вопросы. Побеждает тот, кто набрал больше правильных ответов за раунд.",
        "colors": ((103, 65, 26), (242, 186, 96)),
        "image": "quiz.jpg",
    },
]

CYAN = (58, 226, 255)
PURPLE = (174, 92, 255)
BG_TOP = (7, 10, 20)
BG_BOTTOM = (9, 24, 50)


def enter_soft_fullscreen(window: arcade.Window) -> None:
    """Растягивает окно на весь экран без системного fullscreen-переключения."""
    screen = window.get_window_screen()
    window.set_size(screen.width, screen.height)
    window.set_location(screen.x, screen.y)
    setattr(window, "_soft_fullscreen", True)


def exit_soft_fullscreen(window: arcade.Window) -> None:
    """Возвращает окно к исходному размеру после soft fullscreen."""
    windowed_size = getattr(window, "_windowed_size", (WINDOW_WIDTH, WINDOW_HEIGHT))
    width, height = windowed_size
    screen = window.get_window_screen()
    window.set_size(width, height)
    window.set_location(
        screen.x + (screen.width - width) // 2,
        screen.y + (screen.height - height) // 2,
    )
    setattr(window, "_soft_fullscreen", False)


def is_window_full_like(window: arcade.Window) -> bool:
    """Проверяет, занимает ли окно почти весь экран (или в fullscreen)."""
    if window.fullscreen:
        return True

    win_w, win_h = window.get_size()
    screen = window.get_window_screen()
    tolerance = 2
    return abs(win_w - screen.width) <= tolerance and abs(win_h - screen.height) <= tolerance


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
        "hover": UIInputTextStyle(bg=(10, 20, 56, 230),
                                  border=(122, 234, 255), border_width=2),
        "press": UIInputTextStyle(bg=(12, 25, 63, 240),
                                  border=(144, 241, 255), border_width=2),
        "disabled": UIInputTextStyle(bg=(34, 38, 56, 200),
                                     border=(102, 116, 142), border_width=2),
        "invalid": UIInputTextStyle(bg=(72, 19, 47, 210),
                                    border=(250, 118, 184), border_width=2),
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
            if not self.window:
                return

            if self.window.fullscreen:
                self.window.set_fullscreen(False)
                setattr(self.window, "_soft_fullscreen", False)
                return

            if getattr(self.window, "_soft_fullscreen", False) or is_window_full_like(self.window):
                exit_soft_fullscreen(self.window)
            return

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
        self._draw_vertical_gradient(
            top_color=BG_TOP, bottom_color=BG_BOTTOM, steps=60)
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
            arcade.draw_line(x_bottom, 0, x_top, horizon_y,
                             (38, 123, 210, 40), line_width=1)

        rows = 16
        for i in range(rows):
            t = i / max(rows - 1, 1)
            y = horizon_y + (t * t) * (height * 0.45)
            alpha = int(16 + 42 * (1 - t))
            arcade.draw_line(
                0, y, width, y, (57, 135, 223, alpha), line_width=1)

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

    def _draw_filled_rect(self, left: float, right: float,
                          bottom: float, top: float, color) -> None:
        if hasattr(arcade, "draw_lrbt_rectangle_filled"):
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color)
            return

        if hasattr(arcade, "draw_lrtb_rectangle_filled"):
            arcade.draw_lrtb_rectangle_filled(left, right, top, bottom, color)
            return

        if hasattr(arcade, "draw_lbwh_rectangle_filled"):
            arcade.draw_lbwh_rectangle_filled(
                left, bottom, right - left, top - bottom, color)

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
            arcade.draw_lrbt_rectangle_outline(
                left, right, bottom, top, color, border_width)
            return

        if hasattr(arcade, "draw_lrtb_rectangle_outline"):
            arcade.draw_lrtb_rectangle_outline(
                left, right, top, bottom, color, border_width)
            return

        if hasattr(arcade, "draw_lbwh_rectangle_outline"):
            arcade.draw_lbwh_rectangle_outline(
                left, bottom, right - left, top - bottom, color, border_width)

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
        self._draw_filled_rect(width * 0.20, width * 0.80,
                               height * 0.18, height * 0.78, (5, 12, 30, 120))
        self._draw_outlined_rect(
            width * 0.20, width * 0.80, height * 0.18,
            height * 0.78, (66, 188, 255, 90), 2)
        self._draw_filled_rect(width * 0.25, width * 0.75,
                               height * 0.60, height * 0.66, (20, 52, 110, 80))

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

        Menager().push_message(("login", name))
        self.window.show_view(MainMenuView(player_name=name))


class MainMenuView(NeonBaseView):
    """Главный экран меню проекта."""

    def __init__(self, player_name: str,
                 on_action: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.player_name = player_name
        # Не используем имя с префиксом "on_", чтобы pyglet не принял это за event handler.
        self.action_callback = on_action
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

        if action == "create_lobby":
            try:
                from .x_o_frontend import TicTacToeView
            except ImportError:
                from x_o_frontend import TicTacToeView

            Menager().push_message(("create_game", "X_O"))

            def back_to_menu() -> None:
                self.window.show_view(MainMenuView(self.player_name, self.action_callback))

            self.window.show_view(
                TicTacToeView(player_name=self.player_name, on_back=back_to_menu)
            )
            return

        if action == "games":
            self.window.show_view(
                GamesCatalogView(player_name=self.player_name, on_back=lambda: self.window.show_view(
                    MainMenuView(self.player_name, self.action_callback)
                ))
            )
            return

        self.status_text = f"{self.player_name}: выбрано '{caption}'"
        if self.action_callback:
            self.action_callback(action)


class GamesCatalogView(NeonBaseView):
    """Экран со списком доступных игр и короткими правилами."""

    def __init__(self, player_name: str, on_back: Callable[[], None]):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self._texture_cache: dict[str, arcade.Texture | None] = {}
        self.title_label = arcade.Text(
            "ДОСТУПНЫЕ ИГРЫ",
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=48,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self._build_ui()

    def _build_ui(self) -> None:
        back_button = arcade.gui.UIFlatButton(
            text="НАЗАД В МЕНЮ",
            width=250,
            height=56,
            style=build_primary_button_style(),
        )

        @back_button.event("on_click")
        def on_click(_event):
            self.on_back()

        anchor_widget_cls = getattr(arcade.gui, "UIAnchorWidget", None)
        if anchor_widget_cls is not None:
            self.ui.add(
                anchor_widget_cls(
                    anchor_x="right",
                    anchor_y="top",
                    align_x=-14,
                    align_y=-12,
                    child=back_button,
                )
            )
            return

        anchor_layout = arcade.gui.UIAnchorLayout()
        anchor_layout.add(
            child=back_button,
            anchor_x="right",
            anchor_y="top",
            align_x=-14,
            align_y=-12,
        )
        self.ui.add(anchor_layout)

    def on_draw(self) -> None:
        self.clear()
        self._draw_games_background()
        self._draw_shell()
        self._draw_titles()
        self._draw_game_cards()
        self.ui.draw()

    def _draw_games_background(self) -> None:
        self._draw_vertical_gradient(top_color=BG_TOP, bottom_color=BG_BOTTOM, steps=60)
        self._draw_stars()
        self._draw_grid_perspective()

    def _draw_shell(self) -> None:
        self._draw_filled_rect(
            self.window.width * 0.06,
            self.window.width * 0.94,
            self.window.height * 0.08,
            self.window.height * 0.88,
            (5, 12, 30, 100),
        )
        self._draw_outlined_rect(
            self.window.width * 0.06,
            self.window.width * 0.94,
            self.window.height * 0.08,
            self.window.height * 0.88,
            (66, 188, 255, 72),
            border_width=2,
        )

    def _draw_titles(self) -> None:
        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.94
        self.title_label.draw()

    def _draw_game_cards(self) -> None:
        screen_w = self.window.width
        screen_h = self.window.height
        area_left = screen_w * 0.09
        area_right = screen_w * 0.91
        area_top = screen_h * 0.80
        area_bottom = screen_h * 0.11
        area_w = area_right - area_left
        area_h = area_top - area_bottom

        if screen_w >= 1200:
            cols = 3
        elif screen_w >= 820:
            cols = 2
        else:
            cols = 1

        rows = ceil(len(GAME_CARDS) / cols)
        x_gap = max(18, screen_w * 0.016)
        y_gap = max(16, screen_h * 0.022)
        card_w = (area_w - x_gap * (cols - 1)) / cols
        card_h = (area_h - y_gap * (rows - 1)) / rows

        for idx, game in enumerate(GAME_CARDS):
            row = idx // cols
            col = idx % cols
            left = area_left + col * (card_w + x_gap)
            right = left + card_w
            top = area_top - row * (card_h + y_gap)
            bottom = top - card_h
            self._draw_single_card(left, right, bottom, top, game)

    def _draw_single_card(self, left: float, right: float, bottom: float, top: float, game: dict) -> None:
        self._draw_filled_rect(left, right, bottom, top, (8, 20, 48, 225))
        self._draw_outlined_rect(left, right, bottom, top, (104, 219, 255, 135), border_width=2)

        card_h = top - bottom
        card_w = right - left
        pad_x = max(14, card_w * 0.04)
        pad_y = max(12, card_h * 0.05)
        title_size = 20 if card_w > 420 else 18
        rules_size = 14 if card_w > 420 else 13

        title_y = top - pad_y - 8
        arcade.draw_text(
            game["title"],
            (left + right) / 2,
            title_y,
            (233, 246, 255),
            title_size,
            anchor_x="center",
            anchor_y="center",
            font_name=("Bahnschrift", "Calibri", "Arial"),
            bold=True,
        )

        title_block_h = max(34, card_h * 0.16)
        img_left = left + pad_x
        img_right = right - pad_x
        img_top = top - title_block_h - pad_y
        img_bottom = img_top - card_h * 0.45
        img_col_1, img_col_2 = game["colors"]

        self._draw_game_preview(
            image_name=game.get("image"),
            left=img_left,
            right=img_right,
            bottom=img_bottom,
            top=img_top,
            fallback_color=img_col_1,
        )
        self._draw_outlined_rect(img_left, img_right, img_bottom, img_top, img_col_2, border_width=2)

        rules_top = img_bottom - 10
        rules_bottom = bottom + pad_y
        rules_height = max(42, rules_top - rules_bottom)
        wrapped, rules_size = self._fit_rules_text(
            text=game["rules"],
            text_width=(img_right - img_left),
            text_height=rules_height,
            initial_size=rules_size,
        )
        self._draw_rules_lines(
            lines=wrapped,
            left=img_left,
            top=rules_top,
            bottom=rules_bottom,
            font_size=rules_size,
        )

    def _fit_rules_text(
        self,
        text: str,
        text_width: float,
        text_height: float,
        initial_size: int,
    ) -> tuple[list[str], int]:
        """Подбирает перенос и размер шрифта так, чтобы весь текст влезал в карточку."""
        for size in range(initial_size, 10, -1):
            wrap_width = max(18, int(text_width / (size * 0.58)))
            lines = textwrap.wrap(text, width=wrap_width)
            line_step = int(size * 1.32)
            if len(lines) * line_step <= text_height:
                return lines, size

        size = 10
        wrap_width = max(16, int(text_width / (size * 0.58)))
        lines = textwrap.wrap(text, width=wrap_width)
        max_lines = max(1, int(text_height / int(size * 1.32)))
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip(" .,!?:;") + "..."
        return lines, size

    def _draw_game_preview(
        self,
        image_name: Optional[str],
        left: float,
        right: float,
        bottom: float,
        top: float,
        fallback_color: tuple[int, int, int],
    ) -> None:
        texture = self._get_texture(image_name) if image_name else None
        if texture is None:
            self._draw_filled_rect(left, right, bottom, top, fallback_color)
            return

        # Фон под картинку на случай "полей" при сохранении пропорций.
        self._draw_filled_rect(left, right, bottom, top, (10, 16, 30, 235))

        box_w = right - left
        box_h = top - bottom
        tex_w = max(float(texture.width), 1.0)
        tex_h = max(float(texture.height), 1.0)
        scale = min(box_w / tex_w, box_h / tex_h)

        sprite = arcade.Sprite()
        sprite.texture = texture
        sprite.width = tex_w * scale
        sprite.height = tex_h * scale
        sprite.center_x = (left + right) / 2
        sprite.center_y = (bottom + top) / 2
        sprite_list = arcade.SpriteList()
        sprite_list.append(sprite)
        sprite_list.draw(pixelated=False)

    def _get_texture(self, image_name: str) -> Optional[arcade.Texture]:
        if image_name in self._texture_cache:
            return self._texture_cache[image_name]

        image_path = GAMES_MEDIA_DIR / image_name
        if not image_path.exists():
            self._texture_cache[image_name] = None
            return None

        try:
            texture = arcade.load_texture(str(image_path))
        except Exception:
            texture = None
        self._texture_cache[image_name] = texture
        return texture

    def _draw_rules_lines(
        self,
        lines: list[str],
        left: float,
        top: float,
        bottom: float,
        font_size: int,
    ) -> None:
        """Рисует правила строго построчно в прямоугольной области карточки."""
        line_step = int(font_size * 1.32)
        y = top
        for line in lines:
            if y - line_step < bottom:
                break
            arcade.draw_text(
                line,
                left,
                y,
                (186, 211, 238),
                font_size,
                anchor_x="left",
                anchor_y="top",
                font_name=("Calibri", "Arial"),
            )
            y -= line_step


async def run() -> None:
    window = arcade.Window(
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        title=WINDOW_TITLE,
        fullscreen=False,
        resizable=True,
    )
    setattr(window, "_windowed_size", (WINDOW_WIDTH, WINDOW_HEIGHT))
    enter_soft_fullscreen(window)
    window.show_view(RegistrationView())
    arcade.run()


if __name__ == "__main__":
    asyncio.run(run())
