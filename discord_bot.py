import asyncio
import os
from datetime import datetime, timedelta

import discord
import pytz

import games_management
from logger_config import get_logger

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
timezone = pytz.timezone(os.getenv('TIMEZONE'))

bot = discord.Bot()

_1_MINUTES_IN_SECONDS = 1 * 60
_6_HOURS_IN_SECONDS = 6 * 60 * 60

last_time_update: datetime

logger = get_logger(__name__)


async def games_tracker():
    global last_time_update
    while True:
        logger.debug(f'Tracking games_data')

        time_start_ping = datetime.now(timezone)

        updates = games_management.update_games_data(last_time_update)

        if updates:
            message = '\n'.join(updates)
            logger.debug(f'Sending {message=}')

            last_time_update = datetime.now(timezone)
            games_management.save_last_time_update_to_file(last_time_update, 'last_time_update.dat')

            games_management.save_games_to_file('games_data.dat')

            await bot.get_channel(CHANNEL_ID).send(message)

        time_passed = int((datetime.now(timezone) - time_start_ping).total_seconds())
        logger.debug(f'Tracking took {time_passed=} seconds')

        await asyncio.sleep(max(_1_MINUTES_IN_SECONDS - time_passed, 0))


@bot.event
async def on_ready():
    logger.debug('Bot is up...')
    global last_time_update
    last_time_update = games_management.get_last_time_update_from_file('last_time_update.dat')
    games_management.load_games_from_file('games_data.dat')
    await games_tracker()


@bot.slash_command(name='get_games', description='Get tracked games')
async def get_games(ctx):
    logger.debug('get_games called')
    games = games_management.get_games()

    if not games:
        logger.debug(f'games_data empty')
        await ctx.send_response('You have not entered any game yet')
        return

    await ctx.send_response('\n'.join(games))


@bot.slash_command(name='add_game_by_url', description='Add game by url')
async def add_game_by_url(ctx, game_url):
    global last_time_update
    added, failed_reason, game_name = games_management.add_game_by_url(game_url)
    if added:
        await ctx.send_response(f'{game_name} successfully added')
    else:
        await ctx.send_response(failed_reason)


@bot.slash_command(name='remove_game_by_url', description='Remove game by url')
async def remove_game_by_url(ctx, game_url):
    removed, failed_reason, game_name = games_management.remove_game_by_url(game_url)
    if removed:
        await ctx.send_response(f'{game_name} successfully removed')
    else:
        await ctx.send_response(failed_reason)


@bot.slash_command(name='time_until_next_update')
async def time_until_next_update(ctx):
    logger.debug(f'time_until_next_update called')
    if games_management.is_games_data_empty():
        logger.debug(f'games_data empty')
        await ctx.send_response('as soon as you will add games')
        return

    next_time_update_datetime = last_time_update + timedelta(seconds=_6_HOURS_IN_SECONDS)
    time_until_update = next_time_update_datetime - datetime.now(timezone)
    secs = int(time_until_update.total_seconds())
    if secs <= 5:
        await ctx.send_response('very soon...')
        return

    hours, remainder = divmod(secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    await ctx.send_response(
        f'{hours:02}:{minutes:02}:{seconds:02} left to next update or as soon as any price will be changed'
    )


bot.run(DISCORD_BOT_TOKEN)
