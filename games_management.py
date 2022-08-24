import os
import pickle
from datetime import datetime
from typing import List, Tuple

import pytz

from cdkeys_api import check_valid_cdkeys_game_url, get_cdkeys_game_name_by_url, get_game_details
from logger_config import get_logger

_6_HOURS_IN_SECONDS = 6 * 60 * 60
timezone = pytz.timezone(os.getenv('TIMEZONE'))

games_data = {}

logger = get_logger(__name__)


def update_games_data(last_time_update: datetime = datetime.now(timezone)) -> List[str]:
    time_start_updating = datetime.now(timezone)
    updates = []
    for game_url in games_data:
        name, price, currency = get_game_details(game_url)

        if price == 0.0:
            return []

        if price != games_data[game_url]['last_price']:
            logger.debug(f'{games_data[game_url]} price was updated')
            updates.append(
                f'{name} price was changed from {games_data[game_url]["last_price"]} '
                f'{games_data[game_url]["last_currency"]} to {price} {currency}'
            )
            games_data[game_url].update({'last_price': price, 'last_currency': currency})

        elif (time_start_updating - last_time_update).total_seconds() >= _6_HOURS_IN_SECONDS:
            updates.append(
                f'{name} price is still {games_data[game_url]["last_price"]} '
                f'{games_data[game_url]["last_currency"]}'
            )

    updates.sort()
    return updates


def get_games() -> List[str]:
    if is_games_data_empty():
        logger.debug(f'{games_data=} empty')
        return []

    games = [
        f'{games_data[game_url]["name"]} - {games_data[game_url]["last_price"]} {games_data[game_url]["last_currency"]}'
        for game_url in games_data
    ]
    games.sort()

    logger.debug(f'get_games returned {games=}')

    return games


def add_game_by_url(game_url: str) -> Tuple[bool, str, str]:
    logger.debug(f'Request to add {game_url} to tracked games')
    if not check_valid_cdkeys_game_url(game_url):
        logger.debug(f'Invalid url {game_url=}')
        return False, 'invalid url', ''

    if game_url in games_data:
        logger.debug(f'Already tracked game')
        return False, f'{games_data[game_url]["name"]} have already tracked', games_data[game_url]["name"]

    game_name = get_cdkeys_game_name_by_url(game_url)
    games_data[game_url] = {'name': game_name, 'last_price': 0.0, 'last_currency': ''}
    logger.debug(f'{game_name=} added successfully')
    return True, '', game_name


def remove_game_by_url(game_url: str) -> Tuple[bool, str, str]:
    if game_url not in games_data:
        logger.debug(f'{game_url=} not in tracked games')
        return False, f'{game_url} is not in tracked games', ''

    game_name = games_data.pop(game_url)['name']
    logger.debug(f'{game_name=} removed successfully')
    return True, '', game_name


def load_games_from_file(filename: str) -> None:
    if not os.path.isfile(filename):
        with open(filename, mode='wb') as file:
            pickle.dump({}, file)  # create file and add empty dictionary
        return

    with open(filename, mode='rb') as file:
        file_data = pickle.load(file)
        assert type(file_data) == dict
        global games_data
        games_data = file_data


def save_games_to_file(filename: str) -> None:
    if not games_data:
        return

    with open(filename, mode='wb') as file:
        pickle.dump(games_data, file)


def get_last_time_update_from_file(filename: str) -> datetime:
    if not os.path.isfile(filename):
        now = datetime.now(timezone)
        with open(filename, mode='wb') as file:
            pickle.dump(now, file)  # create file and add datetime.now
        return now

    with open(filename, mode='rb') as file:
        file_data = pickle.load(file)
        assert type(file_data) == datetime
        return file_data


def save_last_time_update_to_file(last_time_update: datetime, filename: str) -> None:
    with open(filename, mode='wb') as file:
        pickle.dump(last_time_update, file)


def is_games_data_empty() -> bool:
    return not games_data
