from toot.asynch.commands import cli
from toot.settings import load_settings

defaults = load_settings().get("commands", {})
cli(default_map=defaults)
