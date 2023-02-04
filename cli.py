import click

from pkg_resources import iter_entry_points

[entry_point] = list(iter_entry_points('console_scripts', name="toot"))

cli = entry_point.resolve()
print(cli)
ctx = click.Context(cli)
commands = getattr(cli, 'commands', {})

print(ctx)
command: click.Command
for name, command in cli.commands.items():
    print(name, command)
    print(command.help)
