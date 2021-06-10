" File with utils for AmoCRM connector "

from __future__ import annotations
from typing import Any, Iterable


import json
import pytz
import datetime 
import loguru


def save_tokens_to_file(access_token:str, refresh_token:str, *args, **kwargs) -> bool:
    """ Function for default save token on you local machine. Using for default on AmoCRM connector.

    Args:
        access_token (str): access token to amocrm
        refresh_token (str): refresh token to amocrm

    Returns:
        bool: Is success update or not
    """
    try:
        with open(kwargs.get("path_to_save_file", "access_tokens.json"), "w", encoding="UTF-8") as file:
            json.dump({
                "time_update": str(datetime.datetime.now(pytz.timezone("Europe/Moscow"))),
                "access_token": access_token,
                "refresh_token": refresh_token
            }, file)
    except OSError as e:
        loguru.logger.error(e)
        return False
    return True

def batch(iterable: Iterable, count_batch: int=50) -> list[Any]:
    """ Batch data to package.

    Args:
        iterable (Iterable): Array ot any iterable object.
        count_batch (int, optional): Batch size. Defaults to 1.

    Returns:
        yield: list with items in count {count_batch}.

    Yields:
        Iterator[yield]: [description]
    """
    
    l = len(iterable)
    for ndx in range(0, l, count_batch):
        yield iterable[ndx:min(ndx + count_batch, l)]