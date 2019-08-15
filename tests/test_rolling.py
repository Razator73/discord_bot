import dice_bot


def test_roll_regex_single():
    rolls = dice_bot.get_roll_vars('4d6+2 keep 2![3]')
    expected = [('4', '6', '+', '2', ' keep ', '2', '!', '3', '')]
    assert rolls == expected


def test_roll_multiple():
    rolls = dice_bot.get_roll_vars('4d6+2 keep 2![3] + '
                                   '2d20-1t1')
    expected = [('4', '6', '+', '2', ' keep ', '2', '!', '3', '+'),
                ('2', '20', '-', '1', 't', '1', '', '', '')]
    assert rolls == expected


def test_bad_roll():
    rolls = dice_bot.get_roll_vars('563Tbs')
    assert rolls == []
