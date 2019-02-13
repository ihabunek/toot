from toot import utils


def test_pad():
    # guitar symbol will occupy two cells, so padded text should be 1
    # character shorter
    text = 'Frank Zappa 🎸'

    # Negative values are basically ignored
    assert utils.pad(text, -100) is text

    # Padding to length smaller than text length does nothing
    assert utils.pad(text, 11) is text
    assert utils.pad(text, 12) is text
    assert utils.pad(text, 13) is text
    assert utils.pad(text, 14) is text

    assert utils.pad(text, 15) == 'Frank Zappa 🎸 '
    assert utils.pad(text, 16) == 'Frank Zappa 🎸  '
    assert utils.pad(text, 17) == 'Frank Zappa 🎸   '
    assert utils.pad(text, 18) == 'Frank Zappa 🎸    '
    assert utils.pad(text, 19) == 'Frank Zappa 🎸     '
    assert utils.pad(text, 20) == 'Frank Zappa 🎸      '


def test_trunc():
    text = 'Frank Zappa 🎸'

    assert utils.trunc(text, 1)  == '…'
    assert utils.trunc(text, 2)  == 'F…'
    assert utils.trunc(text, 3)  == 'Fr…'
    assert utils.trunc(text, 4)  == 'Fra…'
    assert utils.trunc(text, 5)  == 'Fran…'
    assert utils.trunc(text, 6)  == 'Frank…'
    assert utils.trunc(text, 7)  == 'Frank…'
    assert utils.trunc(text, 8)  == 'Frank Z…'
    assert utils.trunc(text, 9)  == 'Frank Za…'
    assert utils.trunc(text, 10) == 'Frank Zap…'
    assert utils.trunc(text, 11) == 'Frank Zapp…'
    assert utils.trunc(text, 12) == 'Frank Zappa…'
    assert utils.trunc(text, 13) == 'Frank Zappa…'

    # Truncating to length larger than text length does nothing
    assert utils.trunc(text, 14) is text
    assert utils.trunc(text, 15) is text
    assert utils.trunc(text, 16) is text
    assert utils.trunc(text, 17) is text
    assert utils.trunc(text, 18) is text
    assert utils.trunc(text, 19) is text
    assert utils.trunc(text, 20) is text


def test_fit_text():
    text = 'Frank Zappa 🎸'

    assert utils.fit_text(text, 1)  == '…'
    assert utils.fit_text(text, 2)  == 'F…'
    assert utils.fit_text(text, 3)  == 'Fr…'
    assert utils.fit_text(text, 4)  == 'Fra…'
    assert utils.fit_text(text, 5)  == 'Fran…'
    assert utils.fit_text(text, 6)  == 'Frank…'
    assert utils.fit_text(text, 7)  == 'Frank…'
    assert utils.fit_text(text, 8)  == 'Frank Z…'
    assert utils.fit_text(text, 9)  == 'Frank Za…'
    assert utils.fit_text(text, 10) == 'Frank Zap…'
    assert utils.fit_text(text, 11) == 'Frank Zapp…'
    assert utils.fit_text(text, 12) == 'Frank Zappa…'
    assert utils.fit_text(text, 13) == 'Frank Zappa…'
    assert utils.fit_text(text, 14) == 'Frank Zappa 🎸'
    assert utils.fit_text(text, 15) == 'Frank Zappa 🎸 '
    assert utils.fit_text(text, 16) == 'Frank Zappa 🎸  '
    assert utils.fit_text(text, 17) == 'Frank Zappa 🎸   '
    assert utils.fit_text(text, 18) == 'Frank Zappa 🎸    '
    assert utils.fit_text(text, 19) == 'Frank Zappa 🎸     '
    assert utils.fit_text(text, 20) == 'Frank Zappa 🎸      '
