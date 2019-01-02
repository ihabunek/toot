from toot import utils


def test_pad():
    text = 'Frank Zappa 🎸'
    padded = utils.pad(text, 14)
    assert padded == 'Frank Zappa 🎸'
    # guitar symbol will occupy two cells, so padded text should be 1
    # character shorter
    assert len(padded) == 13
    # when truncated, … occupies one cell, so we get full length
    padded = utils.pad(text, 13)
    assert padded == 'Frank Zappa …'
    assert len(padded) == 13
