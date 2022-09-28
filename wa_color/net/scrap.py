# -*- coding: utf-8 -*-
"""
Compare changes in lesson plan and class cancellations.
"""
from time import localtime, strftime
import logging

from .private._download import DownloadPlan, DownloadCancel

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


def _get_time() -> str:
    """
    Get current time.

    Format: 1970-01-01 12:00:00.

    Returns:
        str: Current time.
    """
    return strftime("%G-%m-%d %T", localtime())


class Plan:
    def __init__(self, file_instance) -> None:
        """
        Check if lesson plan have changed.

        Write changes to disk if changed occurred.

        Args:
            file_instance (obj): An instance of the File Manager class that accesses JSON files from disk.
        """
        # file instance
        self.file_instance = file_instance
        # webscraper instance
        self._dPlan = DownloadPlan(
            url=file_instance.config["URL"]["plan"],
            pattern=file_instance.config["TARGET"]["group_pattern"],
        )
        return None

    def is_color_changed(self) -> bool:
        """
        Check if main page's background color has changed.

        Write to disk and return True if changes occurred.

        Returns:
            bool: True if changed, False if not changed.
        """
        # load from cache (or disk if not cached)
        temp: dict = self.file_instance.plan
        # compare old color vs. new color
        old_color: str = temp["metadata"]["current_color"]
        new_color: str = self._dPlan.color
        if new_color != old_color:
            # get time
            current_time = _get_time()
            temp["metadata"]["last_change_color"] = current_time
            temp["metadata"]["current_color"] = new_color
            temp["metadata"]["current_iteration"] += 1
            if old_color != "null":  # do not add null value to history
                temp["metadata"]["previous_colors"].update({current_time: old_color})
            logging.info(
                f"found change: background color ('{old_color}' -> '{new_color}'), current iteration is now '{temp['metadata']['current_iteration']}'"
            )
            self.file_instance.plan = temp  # write to disk and reload cache
            return True
        logging.info(
            f"no change found: background color ('{old_color}' == '{new_color}'), current iteration is still '{temp['metadata']['current_iteration']}'"
        )
        return False

    def is_link_changed(self) -> bool:
        """
        Check if link to targeted group has changed.

        Write to disk and return True if changes occurred.

        Returns:
            bool: True if changed, False if not changed.
        """
        # load from cache (or disk if not cached)
        temp: dict = self.file_instance.plan
        # compare old link vs. new link
        old_link: str = temp["metadata"]["current_link"]
        new_link: str = self._dPlan.link
        if new_link != old_link:
            # get time
            current_time = _get_time()
            temp["metadata"]["current_link"] = new_link
            temp["metadata"]["last_change_link"] = current_time
            if old_link != "null":  # do not add null value to history
                temp["metadata"]["previous_links"].update({current_time: old_link})
            logging.info(
                f"found change: link to target lesson plan ('{old_link}' -> '{new_link}')"
            )
            self.file_instance.plan = temp  # write to disk and reload cache
            return True
        logging.info(
            f"no change found: link to target lesson plan ('{old_link}' == '{new_link}')"
        )
        return False

    def is_table_changed(self) -> bool:
        """
        Check if targeted group's lesson plan table has changed.

        Write to disk and return True if changes occurred.

        Returns:
            bool: True if changed, False if not changed.
        """
        # load from cache (or disk if not cached)
        temp: dict = self.file_instance.plan
        # compare old table vs. new table
        # not just keys, because
        old_table: dict = temp["current"]
        new_table: dict = self._dPlan.table
        if new_table != old_table:
            temp["current"] = new_table
            temp["previous"] = old_table
            temp["metadata"]["last_change_table"] = _get_time()
            logging.info("found change: target lesson plan's content")
            self.file_instance.plan = temp  # write to disk and reload cache
            return True
        logging.info("no change found: target lesson plan's content")
        return False

    def reset(self) -> None:
        """
        Purge all cached variables.

        This will cause the web scrapper to download and process webpages again.
        """
        # webscraper instance
        self._dPlan.reset()
        return None


class Cancel:
    """
    Check if class cancellations changed.
    """

    def __init__(self, file_instance) -> None:
        """
        Check if class cancellations have changed.

        Write changes to disk if changed occurred.

        Args:
            file_instance (obj): An instance of the File Manager class that accesses JSON files from disk.
        """
        # file instance
        self.file_instance = file_instance
        # webscraper instance
        self._dCancel = DownloadCancel(url=file_instance.config["URL"]["cancel"])
        return None

    def is_cancellations_changed(self) -> bool:
        """
        Check if class cancellations list has changed.

        Write to disk and return True if changes occurred.

        Returns:
            bool: True if changed, False if not changed.
        """
        # load from cache (or disk if not cached)
        temp: dict = self.file_instance.cancel
        # compare old dict vs. new dict
        # {'2022-09-08': 'XYZ cancels their classes'}
        old_dict: dict = temp["current"]
        new_dict: dict = self._dCancel.cancellations
        if new_dict != old_dict:
            temp["current"] = new_dict
            temp["previous"] = old_dict
            temp["metadata"]["current_iteration"] += 1
            temp["metadata"]["last_change"] = _get_time()
            logging.info(
                f"found change: class cancellations' content, current iteration is now '{temp['metadata']['current_iteration']}'"
            )
            self.file_instance.cancel = temp  # write to disk and reload cache
            return True
        logging.info(
            f"no change found: class cancellations' content, current iteration is still '{temp['metadata']['current_iteration']}'"
        )
        return False

    def reset(self) -> None:
        """
        Purge all cached variables.

        This will cause the web scrapper to download and process webpages again.
        """
        # webscraper instance
        self._dCancel.reset()
        return None
