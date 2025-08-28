"""Simple search modal for entering a query.

Replaces legacy search components.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class SearchModal(ModalScreen[str | None]):
    """Minimal modal dialog to capture a search query."""

    CSS = (
        "SearchModal { align: center middle; }\n"
        "SearchModal .dialog { width: 60; max-width: 90%; padding: 1 2;"
        " border: round $secondary; background: $panel; }\n"
        "SearchModal .actions { dock: bottom; height: 3; }\n"
    )

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self._input = Input(placeholder="Search...", value=initial)

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Search", id="title")
            yield self._input
            with Horizontal(classes="actions"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:  # pragma: no cover - trivial
        self.set_focus(self._input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input is self._input:
            self.dismiss(event.value.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self._input.value.strip())
        elif event.button.id == "cancel":
            self.dismiss(None)

    def on_key(self, event) -> None:  # type: ignore[override]
        if getattr(event, "key", "") == "escape":
            self.dismiss(None)
