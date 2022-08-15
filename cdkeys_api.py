import json
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from logger_config import get_logger

logger = get_logger(__name__)


def load_game_details_by_url(game_url: str) -> dict:
    logger.debug(f'Trying to get {game_url=} details')
    try:
        response = requests.get(game_url)
        html_content = response.content.decode()

        assert response.status_code == 200

        soup = BeautifulSoup(html_content, 'html.parser')
        [res] = [element for element in
                 soup.find_all('script', {'type': 'text/x-magento-init'}) if 'dataDetail' in element.get_text()]

        game_details = json.loads(res.getText())['*']['dataDetail']

        return game_details
    except Exception as ex:
        logger.exception(f'There was an exception, {ex}')


def get_game_details(game_url: str) -> Tuple[str, float, str]:
    game_details = load_game_details_by_url(game_url)
    if not game_details:
        return '', 0.0, ''
    name = game_details['name']
    price = float(game_details['price'])
    currency = game_details['currency']
    return name, price, currency


def get_cdkeys_game_name_by_url(game_url: str) -> str:
    game_details = load_game_details_by_url(game_url)
    return game_details['name']


def check_valid_cdkeys_game_url(game_url):
    logger.debug(f'Checking if {game_url=} is valid')
    try:
        parts = game_url.split()
        assert len(parts) == 1
        [url] = parts
        assert url.startswith('https://www.cdkeys.com/')
        assert requests.get(url).status_code == 200
        logger.debug(f'{game_url=} passed all validation')
        return url
    except Exception as ex:
        logger.debug(f'{game_url=} is invalid url, {ex}')
        return None
