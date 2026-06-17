"""Basic frontend screen for the Quiz game."""

from __future__ import annotations

from typing import Callable, Optional

import arcade
import arcade.gui

try:
    from .frontend import Manager
    from .localization import tr
    from .menu import (
        CYAN,
        NeonBaseView,
        PURPLE,
        build_menu_button_style,
        build_primary_button_style,
    )
except ImportError:
    from frontend import Manager
    from localization import tr
    from menu import (
        CYAN,
        NeonBaseView,
        PURPLE,
        build_menu_button_style,
        build_primary_button_style,
    )


QUESTION_PLACEHOLDER = "quiz.question_placeholder"
ANSWER_PLACEHOLDERS = (
    "quiz.answer_placeholder",
    "quiz.answer_placeholder",
    "quiz.answer_placeholder",
    "quiz.answer_placeholder",
)
ANSWER_LETTERS = ("A", "B", "C", "D")
ANSWER_BLUE = (50, 155, 255)
ANSWER_PINK = (230, 88, 178)
ANSWER_PURPLE = PURPLE
STATUS_TEXT = {
    "waiting": "quiz.waiting",
    "joined": "quiz.joined",
    "start": "quiz.start",
    "answer": "quiz.answer",
    "answered": "quiz.answered",
    "finished": "quiz.finished",
    "leave": "quiz.leave",
}


class QuizView(NeonBaseView):
    """Static visual base for the quiz screen."""

    def __init__(
        self,
        player_name: str = "",
        on_back: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self.manager = Manager()
        self.nicks: list[str] = []
        self.lobby_id: int | None = None
        self.status = "waiting"
        self.error_text = ""
        self.players: list[str] = []
        self.question_index = 0
        self.total_questions = 0
        self.question: str | None = None
        self.options: list[str] = []
        self.answers: dict[str, int] = {}
        self.scores: dict[str, int] = {}
        self.correct_answers: list[dict[str, str]] = []

        self.title_label = arcade.Text(
            tr("game.quiz.title").upper(),
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=56,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.status_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(154, 220, 255),
            font_size=18,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.question_counter_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(154, 220, 255),
            font_size=18,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.question_label = arcade.Text(
            tr(QUESTION_PLACEHOLDER),
            x=0,
            y=0,
            color=(236, 247, 255),
            font_size=24,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
            width=680,
            multiline=True,
            align="center",
        )
        self.hint_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(165, 188, 214),
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
        )
        self.result_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(230, 241, 255),
            font_size=22,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.correct_answers_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(185, 207, 232),
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="top",
        )
        self.panel_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(230, 241, 255),
            font_size=20,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        self.answer_labels = [
            arcade.Text(
                text,
                x=0,
                y=0,
                color=(222, 238, 255),
                font_size=22,
                font_name=("Bahnschrift", "Calibri", "Arial"),
                anchor_x="center",
                anchor_y="center",
            )
            for text in ANSWER_PLACEHOLDERS
        ]

        self._register_responsive_text(self.title_label, 56, 20, 0.42)
        self._register_responsive_text(self.status_label, 18, 10, 0.58)
        self._register_responsive_text(
            self.question_counter_label, 18, 10, 0.36
        )
        self._register_responsive_text(self.question_label, 24, 12, 0.54)
        self._register_responsive_text(self.hint_label, 18, 10, 0.58)
        self._register_responsive_text(self.result_label, 22, 12, 0.54)
        self._register_responsive_text(
            self.correct_answers_label, 18, 10, 0.56
        )
        self._register_responsive_text(self.panel_label, 20, 10, 0.24)
        for label in self.answer_labels:
            self._register_responsive_text(label, 22, 12, 0.24)
        self._build_ui()

    def _build_ui(self) -> None:
        self.start_button = arcade.gui.UIFlatButton(
            text=tr("quiz.start_button"),
            width=190,
            height=64,
            style=build_primary_button_style(),
        )

        @self.start_button.event("on_click")
        def on_start(_event):
            self.manager.push_message("start")

        self.ui.add(self.start_button)

        self.next_button = arcade.gui.UIFlatButton(
            text=tr("quiz.next_button"),
            width=190,
            height=56,
            style=build_primary_button_style(),
        )

        @self.next_button.event("on_click")
        def on_next(_event):
            self.manager.push_message({"action": "next"})

        self.ui.add(self.next_button)

        self.back_button = arcade.gui.UIFlatButton(
            text=tr("quiz.back"),
            width=190,
            height=56,
            style=build_menu_button_style(exit_button=True),
        )

        @self.back_button.event("on_click")
        def on_back(_event):
            self.manager.push_message({"action": "leave_game"})
            if self.on_back is not None:
                self.on_back()

        self.ui.add(self.back_button)

        self._add_locale_toggle()
        self._register_responsive_widget(self.start_button, 190, 64, 110, 38)
        self._register_responsive_button(self.start_button)
        self._register_responsive_widget(self.next_button, 190, 56, 110, 42)
        self._register_responsive_button(self.next_button, 20, 11)
        self._register_responsive_widget(self.back_button, 190, 56, 110, 42)
        self._register_responsive_button(self.back_button)

    def on_update(self, _delta_time: float) -> None:
        """Read minimal quiz statuses from backend."""

        while True:
            status, error = self.manager.pop_status()

            if status is None and error is None:
                return

            if error is not None:
                self.error_text = str(error)

            if isinstance(status, dict) and status.get("game") == "QUIZ":
                self.nicks = status.get("nicks", self.nicks)
                self.lobby_id = status.get("lobby_id", self.lobby_id)
                self.status = status.get("status", self.status)
                self.players = status.get("players", self.players)
                self.question_index = status.get(
                    "question_index", self.question_index
                )
                self.total_questions = status.get(
                    "total_questions", self.total_questions
                )
                self.question = status.get("question", self.question)
                self.options = status.get("options", self.options)
                self.answers = status.get("answers", self.answers)
                self.scores = status.get("scores", self.scores)
                self.correct_answers = status.get(
                    "correct_answers", self.correct_answers
                )
                self.error_text = ""

    def on_mouse_press(
        self,
        x: float,
        y: float,
        _button: int,
        _modifiers: int,
    ) -> None:
        """Отправляет выбранный вариант ответа."""

        if self.status not in ("question", "answer", "answered"):
            return

        if not self.player_name:
            return

        for index, bounds in enumerate(self._answer_bounds()):
            left, right, bottom, top = bounds
            if left <= x <= right and bottom <= y <= top:
                self.manager.push_message(
                    {
                        "action": "answer",
                        "answer": index,
                    }
                )
                return

    def on_draw(self) -> None:
        """Draw the static quiz layout."""

        self.clear()
        self._draw_neon_background()
        self._draw_shell()
        self._draw_lobby_panel()
        self._draw_question_card()
        if self._show_answer_cards():
            self._draw_answer_cards()
        self._draw_text_layer()
        self.ui.draw()

    def _draw_shell(self) -> None:
        width = self.window.width
        height = self.window.height

        self._draw_filled_rect(
            width * 0.16,
            width * 0.84,
            height * 0.14,
            height * 0.78,
            (5, 12, 30, 105),
        )
        self._draw_outlined_rect(
            width * 0.16,
            width * 0.84,
            height * 0.14,
            height * 0.78,
            (66, 188, 255, 80),
            border_width=2,
        )

    def _draw_lobby_panel(self) -> None:
        if self.lobby_id is None:
            return

        width = self.window.width
        height = self.window.height
        scale = min(width / 1280, height / 720, 1.0)
        margin = max(14, 24 * scale)
        panel_width = max(190, 306 * scale)
        panel_height = max(42, 56 * scale)

        self._draw_info_panel(
            left=margin,
            right=margin + panel_width,
            bottom=margin,
            top=margin + panel_height,
            caption=tr("quiz.lobby_id"),
            value=str(self.lobby_id),
        )

    def _draw_info_panel(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        caption: str,
        value: str,
    ) -> None:
        self._draw_filled_rect(left, right, bottom, top, (5, 20, 46, 195))
        self._draw_outlined_rect(left, right, bottom, top, CYAN + (185,), 2)

        self.panel_label.text = f"{caption}: {value}"
        self.panel_label.x = (left + right) / 2
        self.panel_label.y = (bottom + top) / 2
        self.panel_label.draw()

    def _draw_question_card(self) -> None:
        left, right, bottom, top = self._question_bounds()
        self._draw_filled_rect(left, right, bottom, top, (4, 14, 34, 220))
        self._draw_outlined_rect(
            left,
            right,
            bottom,
            top,
            (88, 212, 255, 170),
            border_width=3,
        )

    def _draw_answer_cards(self) -> None:
        for index, bounds in enumerate(self._answer_bounds()):
            left, right, bottom, top = bounds
            colors = self._answer_colors(index)
            if len(colors) == 2:
                center = (left + right) / 2
                self._draw_filled_rect(
                    left, center, bottom, top, colors[0] + (80,)
                )
                self._draw_filled_rect(
                    center, right, bottom, top, colors[1] + (80,)
                )
            else:
                self._draw_filled_rect(
                    left, right, bottom, top, colors[0] + (80,)
                )
            self._draw_outlined_rect(
                left,
                right,
                bottom,
                top,
                CYAN + (190,),
                border_width=2,
            )

    def _draw_text_layer(self) -> None:
        self._refresh_texts()
        self._update_responsive_layout()
        self._position_control_buttons()

        width = self.window.width
        height = self.window.height
        q_left, q_right, q_bottom, q_top = self._question_bounds()

        self.title_label.x = width / 2
        self.title_label.y = height * 0.86
        self.title_label.draw()

        self.status_label.text = self._status_text()
        self.status_label.x = width / 2
        self.status_label.y = q_top + max(14, height * 0.025)
        self.status_label.draw()

        if self.status == "finished":
            self.result_label.text = self._result_text()
            self._fit_responsive_text(self.result_label, q_right - q_left - 32, 12)
            self.result_label.x = (q_left + q_right) / 2
            self.result_label.y = (q_bottom + q_top) / 2
            self.result_label.draw()

            self.correct_answers_label.text = self._correct_answers_text()
            self._fit_responsive_text(
                self.correct_answers_label,
                q_right - q_left - 32,
                10,
            )
            self.correct_answers_label.x = (q_left + q_right) / 2
            self.correct_answers_label.y = q_bottom - max(34, height * 0.04)
            self.correct_answers_label.draw()
        else:
            question_width = q_right - q_left - 32
            self.question_counter_label.text = self._question_counter_text()
            self.question_counter_label.x = (q_left + q_right) / 2
            self.question_counter_label.y = q_top - max(24, height * 0.035)
            self.question_counter_label.draw()

            self.question_label.text = self._question_text()
            self.question_label.width = question_width
            self._fit_responsive_text(
                self.question_label,
                question_width,
                12,
            )
            self.question_label.x = (q_left + q_right) / 2
            self.question_label.y = q_bottom + (q_top - q_bottom) * 0.40
            self.question_label.draw()

        if self._show_answer_cards():
            for label, text, bounds in zip(
                self.answer_labels,
                self._answer_texts(),
                self._answer_bounds(),
            ):
                left, right, bottom, top = bounds
                label.text = text
                self._fit_responsive_text(label, right - left - 24, 12)
                label.x = (left + right) / 2
                label.y = (bottom + top) / 2
                label.draw()

        self.hint_label.x = width / 2
        self.hint_label.y = height * 0.18
        self.hint_label.draw()

    def _position_control_buttons(self) -> None:
        width = self.window.width
        height = self.window.height
        scale = min(width / 1280, height / 720, 1.0)
        panel_margin = max(14, 24 * scale)
        panel_width = max(190, 306 * scale)
        button_gap = max(8, 14 * scale)

        start_left = (width - self.start_button.width) / 2
        start_bottom = panel_margin if self._show_start_button() else -10000
        self.start_button.move(
            dx=start_left - self.start_button.left,
            dy=start_bottom - self.start_button.bottom,
        )

        next_left = width - panel_margin - self.next_button.width
        next_bottom = panel_margin if self.status == "answered" else -10000
        self.next_button.move(
            dx=next_left - self.next_button.left,
            dy=next_bottom - self.next_button.bottom,
        )

        back_left = panel_margin + panel_width + button_gap
        self.back_button.move(
            dx=back_left - self.back_button.left,
            dy=panel_margin - self.back_button.bottom,
        )

    def _refresh_texts(self) -> None:
        super()._refresh_texts()
        self.title_label.text = tr("game.quiz.title").upper()
        self.start_button.text = tr("quiz.start_button")
        self.next_button.text = tr("quiz.next_button")
        self.back_button.text = tr("quiz.back")
        self.hint_label.text = self._meta_text()

    def _status_text(self) -> str:
        if self.error_text:
            return self.error_text

        if self.status in ("question", "answer"):
            if self.player_name in self.answers:
                return tr("quiz.wait_answer")
            return tr("quiz.choose_answer")

        status_key = STATUS_TEXT.get(self.status)
        return tr(status_key) if status_key else self.status

    def _show_start_button(self) -> bool:
        return self.status in ("waiting", "joined", "leave")

    def _show_answer_cards(self) -> bool:
        return self.status in ("question", "answer", "answered")

    def _meta_text(self) -> str:
        if self.lobby_id is None:
            return tr("quiz.empty_lobby")

        players = "  /  ".join(self.nicks) if self.nicks else "-"
        return tr("quiz.lobby", players=players)

    def _question_counter_text(self) -> str:
        if self.total_questions:
            return tr(
                "quiz.question_counter",
                current=self.question_index + 1,
                total=self.total_questions,
            )

        return ""

    def _question_text(self) -> str:
        if self.question:
            return tr(self.question)

        return tr("quiz.question_placeholder")

    def _answer_texts(self) -> list[str]:
        if not self.options:
            return [
                f"{ANSWER_LETTERS[index]}. {tr(option_key)}"
                for index, option_key in enumerate(ANSWER_PLACEHOLDERS)
            ]

        return [
            f"{ANSWER_LETTERS[index]}. {tr(answer)}"
            for index, answer in enumerate(self.options[:4])
        ]

    def _result_text(self) -> str:
        players = self.players or self.nicks
        score_lines = [
            f"{player}: {self.scores.get(player, 0)}"
            for player in players
        ]
        text = [tr("quiz.score_title"), *score_lines]

        return "\n".join(text)

    def _correct_answers_text(self) -> str:
        answers = [tr("quiz.correct_answers")]

        for index, item in enumerate(self.correct_answers):
            correct = item.get("correct", "-")
            answers.append(f"{index + 1}. {tr(correct)}")

        return "\n".join(answers)

    def _answer_colors(self, answer_index: int) -> list[tuple[int, int, int]]:
        if self.status == "finished":
            return [CYAN]

        selected_players = [
            player
            for player, index in self.answers.items()
            if index == answer_index
        ]

        if not selected_players:
            return [CYAN]

        if len(selected_players) > 1:
            return [ANSWER_BLUE, ANSWER_PINK]

        players = self.players or self.nicks
        player = selected_players[0]
        if players and player == players[0]:
            return [ANSWER_BLUE]

        return [ANSWER_PINK]

    def _question_bounds(self) -> tuple[float, float, float, float]:
        width = self.window.width
        height = self.window.height

        return (
            width * 0.25,
            width * 0.75,
            height * 0.52,
            height * 0.68,
        )

    def _answer_bounds(self) -> list[tuple[float, float, float, float]]:
        width = self.window.width
        height = self.window.height
        left = width * 0.25
        right = width * 0.75
        gap_x = max(12, width * 0.018)
        gap_y = max(10, height * 0.022)
        card_width = (right - left - gap_x) / 2
        card_height = height * 0.09
        top = height * 0.44

        return [
            (left, left + card_width, top - card_height, top),
            (left + card_width + gap_x, right, top - card_height, top),
            (
                left,
                left + card_width,
                top - card_height * 2 - gap_y,
                top - card_height - gap_y,
            ),
            (
                left + card_width + gap_x,
                right,
                top - card_height * 2 - gap_y,
                top - card_height - gap_y,
            ),
        ]
