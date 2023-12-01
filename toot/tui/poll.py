import urwid

from toot import api
from toot.exceptions import ApiError
from toot.utils.datetime import parse_datetime
from .widgets import Button, CheckBox, RadioButton
from .richtext import html_to_widgets


class Poll(urwid.ListBox):
    """View and vote on a poll"""

    def __init__(self, app, user, status):
        self.status = status
        self.app = app
        self.user = user
        self.poll = status.original.data.get("poll")
        self.button_group = []
        self.api_exception = None
        self.setup_listbox()

    def setup_listbox(self):
        actions = list(self.generate_contents(self.status))
        walker = urwid.SimpleListWalker(actions)
        super().__init__(walker)

    def build_linebox(self, contents):
        contents = urwid.Pile(list(contents))
        contents = urwid.Padding(contents, left=1, right=1)
        return urwid.LineBox(contents)

    def vote(self, button_widget):
        poll = self.status.original.data.get("poll")
        choices = []
        for idx, button in enumerate(self.button_group):
            if button.get_state():
                choices.append(idx)

        if len(choices):
            try:
                response = api.vote(self.app, self.user, poll["id"], choices=choices)
                self.status.original.data["poll"] = response
                self.api_exception = None
                self.poll["voted"] = True
                self.poll["own_votes"] = choices
            except ApiError as exception:
                self.api_exception = exception
            finally:
                self.setup_listbox()

    def generate_poll_detail(self):
        poll = self.poll

        self.button_group = []  # button group
        for idx, option in enumerate(poll["options"]):
            voted_for = (
                poll["voted"] and poll["own_votes"] and idx in poll["own_votes"]
            )

            if poll["voted"] or poll["expired"]:
                prefix = " ✓  " if voted_for else "    "
                yield urwid.Text(("dim", prefix + f'{option["title"]}'))
            else:
                if poll["multiple"]:
                    checkbox = CheckBox(f'{option["title"]}')
                    self.button_group.append(checkbox)
                    yield checkbox
                else:
                    yield RadioButton(self.button_group, f'{option["title"]}')

        yield urwid.Divider()

        poll_detail = "Poll · {} votes".format(poll["votes_count"])

        if poll["expired"]:
            poll_detail += " · Closed"

        if poll["expires_at"]:
            expires_at = parse_datetime(poll["expires_at"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            poll_detail += " · Closes on {}".format(expires_at)

        yield urwid.Text(("dim", poll_detail))

    def generate_contents(self, status):
        yield urwid.Divider()

        widgetlist = html_to_widgets(status.data["content"])

        for line in widgetlist:
            yield (line)

        yield urwid.Divider()
        yield self.build_linebox(self.generate_poll_detail())
        yield urwid.Divider()

        if self.poll["voted"]:
            yield urwid.Text(("grey", "< Already Voted >"))
        elif not self.poll["expired"]:
            yield Button("Vote", on_press=self.vote)

        if self.api_exception:
            yield urwid.Divider()
            yield urwid.Text("warning", str(self.api_exception))
