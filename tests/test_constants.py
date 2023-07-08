from toot.tui.constants import PALETTE, MONO_PALETTE


def test_palette():
    # for every entry in PALETTE, there must be
    # a corresponding entry in MONO_PALETTE
    for pal in PALETTE:
        matches = [item for item in MONO_PALETTE if item[0] == pal[0]]
        assert len(matches) > 0, f"{pal}, present in PALETTE, missing from MONO_PALETTE"

    # for every entry in MONO_PALETTE, there must be
    # a corresponding entry in PALETTE
    for pal in MONO_PALETTE:
        matches = [item for item in PALETTE if item[0] == pal[0]]
        assert len(matches) > 0, f"{pal}, present in MONO_PALETTE, missing from PALETTE"
