import sys
from toot.cli import cli
from toot.exceptions import ConsoleError
from toot.output import print_err
from toot.settings import load_settings

try:
    defaults = load_settings().get("commands", {})
    cli(default_map=defaults)
except ConsoleError as ex:
    print_err(str(ex))
    sys.exit(1)
except KeyboardInterrupt:
    print_err("Aborted")
    sys.exit(1)
