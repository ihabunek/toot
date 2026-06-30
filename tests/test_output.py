from wcwidth import wcswidth

from toot.output import print_table


def test_print_table_aligns_wide_characters(capsys):
    # The Title column mixes ASCII and CJK entries. CJK characters occupy two
    # terminal cells each, so column widths and padding must be measured in
    # display columns rather than character count. When they are, every
    # rendered row occupies the same total display width.
    print_table(
        ["ID", "Title"],
        [
            ["1", "Hello"],
            ["2", "日本語"],
        ],
    )

    lines = capsys.readouterr().out.splitlines()
    display_widths = {wcswidth(line) for line in lines}

    assert len(display_widths) == 1
