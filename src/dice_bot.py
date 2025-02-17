#!/usr/bin/env pipenv-shebang
import argparse
import os
import random
import re
from pathlib import Path

import discord
import razator_utils
from discord.ext import commands
from dotenv import load_dotenv


def get_roll_vars(roll_string):
    dice_regex = re.compile(r"(\d*)d(\d+)([+-])?(\d*)(\s?keep\s?|\s?toss\s?|\s?drop\s?|[ktd])?"
                            r"(\d*)(?:(!)(?:\[(\d+)\])?)?(?:\s+([+-])\s+)?",
                            re.IGNORECASE | re.VERBOSE)

    rolls = dice_regex.findall(roll_string)

    return rolls


def init_roll_vars(roll):
    num_dice, sides, sign, mod, keep_toss, toss_num, exp, exp_times, next_sign = roll
    keep_toss = keep_toss.strip()
    int_mod = int(sign + mod) if sign and mod else 0
    num_dice = int(num_dice) if num_dice else 1
    toss_num = int(toss_num) if toss_num else 0
    sides = int(sides) if sides else 10
    exp_times = int(exp_times) if exp_times else 3

    return num_dice, sides, sign, mod, int_mod, keep_toss, toss_num, exp, exp_times, next_sign


def perform_roll(num_dice, sides, keep_toss, toss_num, exp, exp_times):
    rolled = []
    sum_rolled = []
    for die in range(num_dice):
        roll_num = random.randint(1, sides)
        if exp and roll_num == sides:
            exp_roll = [roll_num]
            i = 0
            roll_sum = roll_num
            while roll_num == sides and i < exp_times:
                roll_num = random.randint(1, sides)
                exp_roll.append(roll_num)
                i += 1
                roll_sum += roll_num
            rolled.append(exp_roll)
            sum_rolled.append(roll_sum)
        else:
            rolled.append(roll_num)
            sum_rolled.append(roll_num)

    # Keep or toss the higher rolls.
    discarded = []
    if keep_toss and keep_toss.lower() in ('k', 'keep'):
        for i in range(len(rolled) - toss_num):
            discard_index = sum_rolled.index(min(sum_rolled))
            discarded.append(rolled.pop(discard_index))
            sum_rolled.pop(discard_index)
    if keep_toss and keep_toss.lower() in ('t', 'toss'):
        for i in range(toss_num):
            discard_index = sum_rolled.index(max(sum_rolled))
            discarded.append(rolled.pop(discard_index))
            sum_rolled.pop(discard_index)
    if keep_toss in ('d', 'drop'):
        for i in range(toss_num):
            discard_index = sum_rolled.index(min(sum_rolled))
            discarded.append(rolled.pop(discard_index))
            sum_rolled.pop(discard_index)

    return rolled, sum_rolled, discarded


def get_roll_string(all_rolled):
    # Print out the string that will show the sum of the roll.
    total = 0
    overall_sum_str = '[' if len(all_rolled) > 1 else ''
    add_or_sub = 1
    for die_roll in all_rolled:
        rolled, sum_rolled, discarded, mod, int_mod, sign, next_sign = die_roll
        total += add_or_sub * (sum(sum_rolled) + int_mod)
        sum_str = ' + '.join('{{{}}}'.format(' + '.join(str(y) for y in x))
                             if type(x) == list else str(x) for x in rolled)
        sum_str += ' + ~~{}~~'.format(' + '.join('[{}]'.format(' + '.join(str(y) for y in x))
                                                 if type(x) == list else str(x) for x in discarded)) \
            if discarded else ''
        if int_mod:
            sum_str = '({}) {} {}'.format(sum_str, sign, mod)
        overall_sum_str += f'{sum_str}]' if len(all_rolled) > 1 else sum_str
        add_or_sub = 1 if next_sign == '+' else -1
        if next_sign:
            overall_sum_str += f' {next_sign} ['
    overall_sum_str += f' = {total}'
    return overall_sum_str


def dice_roll(roll_string):
    """ This takes a string in the form of typical DnD rolls (eg 2d8 or 1d20)
        These rolls can take modifiers and specify whether the number of high
        rolls that should be kept or tossed (eg 5d8+3 keep 3)"""

    rolls = get_roll_vars(roll_string)
    try:
        assert rolls, "Didn't recognize the roll, try again"
    except AssertionError:
        return "I didn't recognize \"{}\" as a valid roll".format(roll_string)
    all_rolled = []
    for roll in rolls:
        num_dice, sides, sign, mod, int_mod, keep_toss, toss_num, exp, exp_times, next_sign = init_roll_vars(roll)

        try:
            assert num_dice > toss_num, 'Can not toss/keep/drop more than the rolled number of dice'
        except AssertionError:
            return 'Invalid roll. Need to roll more dice than are kept/tossed/dropped.'

        rolled, sum_rolled, discarded = perform_roll(num_dice, sides, keep_toss, toss_num, exp, exp_times)
        all_rolled.append((rolled, sum_rolled, discarded, mod, int_mod, sign, next_sign))

    return get_roll_string(all_rolled)


def bot_help():
    bot_commands = {'roll': {'function': dice_roll,
                             'description': 'Used to roll dice (eg. 2d6+3)'},
                    'help': {'function': bot_help,
                             'description': 'list available commands'}}
    command_str = [f'{x}\t{y["description"]}'for x, y in bot_commands.items()]
    return 'Available commands are:\n\t```/{}```'.format('\n/'.join(command_str))


def run(logger):
    bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

    @bot.event
    async def on_ready():
        logger.info(f'{bot.user} has connected to Discord!')

    @bot.command()
    async def roll(ctx, *roll_args):
        """
        This is the help text
        """
        roll_str = ' '.join([*roll_args])
        await ctx.send(dice_roll(roll_str))

    bot.run(os.environ['DISCORD_TOKEN'])


if __name__ == '__main__':
    load_dotenv()
    arg_parser = argparse.ArgumentParser(prog='dice_bot', description='Discord dice rolling bot')
    arg_parser.add_argument('-v', '--stdout', action='store_true', help='Print logs to stdout')
    args = arg_parser.parse_args()

    if args.stdout:
        main_logger = razator_utils.log.get_stout_logger('dice_bot', 'INFO')
    else:
        log_file = Path.home() / 'logs' / 'dice_bot.log'
        log_file.parent.mkdir(exist_ok=True)
        main_logger = razator_utils.log.get_file_logger('dice_bot', log_file, 'INFO')
    # noinspection PyBroadException
    try:
        run(main_logger)
    except Exception:
        main_logger.exception()
