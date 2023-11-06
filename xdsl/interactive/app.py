"""
This app allows you to paste xDSL IR into the Input TextArea, select a pass (or multiple passes) to be applied on the input IR
and subsequently the IR generated by the application of the selected pass(es) is displayed in the Output TextArea. The selected
passes are displayed in the top right "Selecred passes/query" box. The "Condense" button filters the pass selection list to
display passes that change the IR, or require arguments to be executed (and thus "may" change the IR). The "Uncondense" button
returns the selection list to contain all the passes. The "Clear Passes" Button removes the application of the selected passes.
The "Copy Query" Button allows the user to copy the selected passes/query that they have so far selected (i.e. copy the top right
box).

This app is still under construction.
"""

from io import StringIO

from rich.style import Style
from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, TextArea
from textual.widgets.text_area import TextAreaTheme

from xdsl.dialects import builtin
from xdsl.ir import MLContext
from xdsl.parser import Parser
from xdsl.printer import Printer
from xdsl.tools.command_line_tool import get_all_dialects


def transform_input(input_text: str) -> builtin.ModuleOp:
    """
    Function that takes the input IR, the list of passes to be applied, and applies the passes to the IR.
    Returns the module (after pass is applied).
    """
    ctx = MLContext(True)
    for dialect in get_all_dialects():
        ctx.load_dialect(dialect)

    parser = Parser(ctx, input_text)
    module = parser.parse_module()

    return module


class OutputTextArea(TextArea):
    """Used to prevent users from being able to change/alter the Output TextArea"""

    async def _on_key(self, event: events.Key) -> None:
        event.prevent_default()


class InputApp(App[None]):
    """
    Class buildling the Interactive Compilation App. Uses Textual Python to construct reactive variables on the App, Event,
    Widget classes etc. The UI is derived from those values as they change.
    """

    CSS_PATH = "app.tcss"
    text: str

    output_ir = reactive("")

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit_app", "Quit")]

    def __init__(self, text: str | None = None):
        """Initialization function"""
        if text is None:
            text = ""
        self.text = text
        super().__init__()

    def compose(self) -> ComposeResult:
        """
        Creates the required widgets, events, etc.
        Get the list of xDSL passes, add them to an array in "Selection" format (so it can be added to a Selection List)
        and sort the list in alphabetical order.
        """

        my_theme = TextAreaTheme(
            name="my_cool_theme",
            base_style=Style(bgcolor="white"),
            syntax_styles={
                "string": Style(color="red"),
                "comment": Style(color="magenta"),
            },
        )

        text_area = TextArea(self.text, id="input")
        output_text_area = OutputTextArea("No output", id="output")

        with Horizontal(id="input_output"):
            with Vertical(id="input_container"):
                yield text_area
                text_area.register_theme(my_theme)
                text_area.theme = "my_cool_theme"
            with Vertical(id="output_container"):
                yield output_text_area
                output_text_area.register_theme(my_theme)
                output_text_area.theme = "my_cool_theme"
        yield Footer()

    def compute_output_ir(self) -> None:
        input = self.query_one("#input", TextArea)

        input_text = input.text
        try:
            module = transform_input(input_text)

            output_stream = StringIO()
            Printer(output_stream).print(module)
            output_text = output_stream.getvalue()
        except Exception as e:
            output_text = str(e)

        output_ir = output_text
        self.query_one("#output", TextArea).load_text(output_ir)

    def on_mount(self) -> None:
        """On App Mount, add titles + execute()"""
        self.query_one("#input_container").border_title = "Input xDSL IR"
        self.query_one("#output_container").border_title = "Output xDSL IR"

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_quit_app(self) -> None:
        """An action to quit the app."""
        self.exit()

    @on(TextArea.Changed, "#input")
    def on_input_changed(self, event: TextArea.Changed):
        """When the input TextArea changes, call exectue function"""
        # self.execute(event.text_area)
        self.compute_output_ir()


if __name__ == "__main__":
    app = InputApp(None)
    app.run()
