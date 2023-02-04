import asyncio
import httpx
import logging
import urwid

from toot import App, User, config, __version__
from urwid import font

from toot.tui.constants import PALETTE

logging.basicConfig(filename="debug.log", level=logging.INFO)
logger = logging.getLogger(__name__)

urwid.set_encoding('UTF-8')


class Toot:
    def __init__(self, user: User, app: App):
        logger.info("init")
        self.user = user
        self.app = app
        self.config = config.load_config()
        self.layout = loading_screen()

        # Default max status length, updated on startup
        self.max_toot_chars = 500

    def create_layout(self):
        self.txt = urwid.Text(u"Hello World")
        return urwid.Filler(self.txt, "top")

    async def boot(self):
        logger.info("boot")
        await asyncio.gather(
            self.load_max_toot_chars()
        )
        logger.info(f"self.max_toot_chars: {self.max_toot_chars}")

    async def load_max_toot_chars(self):
        """Some instances may have a non-default limit on toot size."""
        instance = await get_instance(self.app.instance)
        if "max_toot_chars" in instance:
            self.max_toot_chars = instance["max_toot_chars"]

    def run(self):
        asyncio_loop = asyncio.get_event_loop()
        main_loop = urwid.MainLoop(
            self.layout,
            event_loop=urwid.AsyncioEventLoop(loop=asyncio_loop),
            palette=PALETTE,
            unhandled_input=self.handle_keypress
        )
        self._boot_task = asyncio_loop.create_task(self.boot())
        main_loop.run()

    def handle_keypress(self, key):
        if key.lower() == "q":
            raise urwid.ExitMainLoop()


async def get_instance(domain):
    url = "https://{}/api/v1/instance".format(domain)
    logger.info(f">>> {url}")

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()


def main():
    user, app = config.get_active_user_app()
    if user and app:
        Toot(user, app).run()


def loading_screen():
    # NB: Padding with width="clip" will convert the fixed BigText widget
    # to a flow widget so it can be used in a Pile.
    big_text = "Toot {}".format(__version__)
    big_text = urwid.BigText(("intro_bigtext", big_text), font.Thin6x6Font())
    big_text = urwid.Padding(big_text, align="center", width="clip")

    contents = urwid.Pile([
        big_text,
        urwid.Divider(),
        urwid.Text([
            "Maintained by ",
            ("intro_smalltext", "@ihabunek"),
            " and contributors"
        ], align="center"),
        urwid.Divider(),
        urwid.Text(("intro_smalltext", "Loading toots..."), align="center"),
    ])

    return urwid.Filler(contents)
