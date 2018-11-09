import discord
import re
import random
import os


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    com_regex = re.compile(r'^\\(\w+)\s*(.*)?')

    if com_regex.search(message.content):
        command, instructions = com_regex.search(message.content).groups()
        instructions = instructions.lstrip() if instructions else instructions
        msg = commands[command](instructions)
        await client.send_message(message.channel, msg)


@client.event
async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('-------')


def dice_roll(roll_string):
    """ This takes a string in the form of typical DnD rolls (eg 2d8 or 1d20)
        These rolls can take modifiers and specify whether the number of high
        rolls that should be kept or tossed (eg 5d8+3 keep 3)"""
    dice_regex = re.compile(r"(\d*)d(\d+)\s*([+-])?(\d*)\s*(keep|toss|[ktd]|drop)?\s*(\d*)\s*",
                            re.IGNORECASE | re.VERBOSE)
    if not roll_string:
        return 'You have to try and roll something.'

    roll = dice_regex.search(roll_string)
    try:
        assert roll, "Didn't recognize the roll, try again"
    except AssertionError:
        return "I didn't recognize \"{}\" as a valid roll".format(roll_string)
    num_dice, sides, sign, mod, keep_toss, toss_num = roll.groups()
    int_mod = int(sign + mod) if sign and mod else 0
    num_dice = int(num_dice) if num_dice else 1
    toss_num = int(toss_num) if toss_num else 0
    sides = int(sides)

    rolled = []
    for die in range(num_dice):
        rolled.append(random.randint(1, sides))

    # Keep or toss the higher rolls.
    discarded = []
    if keep_toss and keep_toss.lower() in ('k', 'keep'):
        for i in range(len(rolled) - toss_num):
            discarded.append(min(rolled))
            rolled.remove(min(rolled))
    if keep_toss and keep_toss.lower() in ('t', 'toss'):
        for i in range(toss_num):
            discarded.append(max(rolled))
            rolled.remove(max(rolled))
    if keep_toss in ('d', 'drop'):
        for i in range(toss_num):
            discarded.append(min(rolled))
            rolled.remove(min(rolled))

    # Print out the string that will show the sum of the roll.
    total = sum(rolled) + int_mod
    sum_str = ' + '.join(str(x) if x != sides else '**{}**'.format(x) for x in rolled)
    sum_str += ' + {}'.format(' + '.join('~~{}~~'.format(x) for x in discarded)) if discarded else ''
    if not int_mod:
        sum_str += ' = {}'.format(total)
    else:
        sum_str = '({}) {} {} = {}'.format(sum_str, sign, mod, total)
    return sum_str


def bot_help(message):
    if message:
        pass
    return 'Available commands are:\n\n\t\\{}'.format('\n\t\\'.join(commands.keys()))


commands = {'roll': dice_roll,
            'help': bot_help}

client.run(os.environ.get('DISCORD_TOKEN'))
