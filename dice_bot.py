import discord
import re
import random
import json


client = discord.Client()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    com_regex = re.compile(r'^/(\w+)\s*(.*)?')

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
    # TODO: multiple dice types in the same roll eg. 'd20 + 3d6' roll a d20 and 3d6 (right now this is seen as mod and drop 6)
    dice_regex = re.compile(r"^(\d*)(?:d(\d+))?\s*([+-])?(\d*)\s*(keep|toss|drop|[ktd])?"
                            r"\s*(\d*)\s*(?:(!)(?:\[(\d+)\])?)?\s*$",
                            re.IGNORECASE | re.VERBOSE)

    roll = dice_regex.search(roll_string)
    try:
        assert roll, "Didn't recognize the roll, try again"
    except AssertionError:
        return "I didn't recognize \"{}\" as a valid roll".format(roll_string)
    num_dice, sides, sign, mod, keep_toss, toss_num, exp, exp_times = roll.groups()
    int_mod = int(sign + mod) if sign and mod else 0
    num_dice = int(num_dice) if num_dice else 1
    toss_num = int(toss_num) if toss_num else 0
    sides = int(sides) if sides else 10
    exp_times = int(exp_times) if exp_times else 3

    try:
        assert num_dice > toss_num, 'Can not toss/keep/drop more than the rolled number of dice'
    except AssertionError:
        return 'Invalid roll. Need to roll more dice than are kept/tossed/dropped.'

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

    # Print out the string that will show the sum of the roll.
    total = sum(sum_rolled) + int_mod
    sum_str = ' + '.join('[{}]'.format(' + '.join(str(y) for y in x)) if type(x) == list else str(x) for x in rolled)
    sum_str += ' + ~~{}~~'.format(' + '.join('[{}]'.format(' + '.join(str(y) for y in x))
                                             if type(x) == list else str(x) for x in discarded)) if discarded else ''
    if not int_mod:
        sum_str += ' = {}'.format(total)
    else:
        sum_str = '({}) {} {} = {}'.format(sum_str, sign, mod, total)
    return sum_str


def bot_help(message):
    if message:
        pass
    return 'Available commands are:\n\n\t```/{}```'.format('```\n\t```/'.join(commands.keys()))


commands = {'roll': dice_roll,
            'help': bot_help}

with open('token.json') as cred_file:
    discord_token = json.load(cred_file)['DISCORD_TOKEN']
client.run(discord_token)
