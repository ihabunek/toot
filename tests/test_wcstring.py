from wcwidth import iter_graphemes, wcswidth

from toot.wcstring import trunc, wc_wrap

# Each of these is one grapheme cluster: what a terminal draws as a single
# character, made of several code points.
FAMILY = "\U0001f468‍\U0001f469‍\U0001f467‍\U0001f466"
RAINBOW_FLAG = "\U0001f3f3️‍\U0001f308"
SKIN_TONE = "\U0001f44d\U0001f3fd"
FLAG = "\U0001f1ef\U0001f1f5"
KEYCAP = "1️⃣"

GLYPHS = [FAMILY, RAINBOW_FLAG, SKIN_TONE, FLAG, KEYCAP]


def cluster_boundaries(text):
    """Character offsets at which a grapheme cluster may start or end."""
    offsets, offset = {0}, 0
    for cluster in iter_graphemes(text):
        offset += len(cluster)
        offsets.add(offset)
    return offsets


def test_trunc_does_not_cut_through_a_glyph():
    # Truncation decides how much to remove by measuring; measuring per code
    # point rather than per cluster makes it stop in the middle of a glyph,
    # leaving a dangling zero-width joiner or a lone regional indicator.
    for glyph in GLYPHS:
        text = glyph * 6
        boundaries = cluster_boundaries(text)
        for length in range(2, 14):
            result = trunc(text, length)
            kept = result[:-1] if result.endswith("…") else result
            assert text.startswith(kept)
            assert len(kept) in boundaries, (
                f"trunc({glyph!r} * 6, {length}) cut at character {len(kept)}, "
                "which is inside a glyph"
            )


def test_trunc_result_fits_the_requested_width():
    for glyph in GLYPHS:
        text = glyph * 6
        for length in range(2, 14):
            result = trunc(text, length)
            assert wcswidth(result) <= length


def test_wc_wrap_lines_fit_the_requested_width():
    # A keycap is three code points and two columns; added up per code point
    # it comes to one, so a line of them is wrapped a column too late.
    for glyph in GLYPHS:
        text = " ".join([glyph * 3] * 4)
        for length in range(4, 16):
            for line in wc_wrap(text, length):
                assert wcswidth(line) <= length, (
                    f"wc_wrap({glyph!r}..., {length}) produced a line of "
                    f"{wcswidth(line)} columns"
                )
