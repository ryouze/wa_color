# -*- coding: utf-8 -*-
"""
Convert a Response object to another type: soup.
"""
import logging

from bs4 import BeautifulSoup

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


def soup(obj) -> BeautifulSoup:
    """
    Convert Response object to BeautifulSoup object

    Suggested usage: webscraping.

    Args:
        obj (requests.Response): Response object (e.g., r = requests.get(url)).

    Returns:
        BeautifulSoup: Soup object (e.g., table = soup.table).
    """
    try:
        return BeautifulSoup(obj.content, features="html.parser")
    except Exception as e:
        logging.error(f"failed to convert to soup ({e})")
        raise
