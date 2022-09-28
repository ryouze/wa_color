# -*- coding: utf-8 -*-
"""
Setup App and Debug class for importing within main.py at root.
"""
import logging
from random import randint
from time import sleep

from requests.exceptions import ConnectionError, HTTPError, Timeout

from .communication.mail import Mail
from .disk.file import FileManager
from .disk.html import HtmlManager
from .net.scrap import Cancel, Plan

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class App:
    """
    Webscraper for WA website that runs as an infinite blocking loop every X seconds.
    Example usage:
    >>> app = App()
    >>> app.run()
    """

    def __init__(self, reset: bool = False) -> None:
        """
        Setup main web scrapper app.

        Instances:
        * file_manager() - load/save files to disk.
        * plan_manager() - scrap and compare WA lesson plan.
        * cancel_manager() - scrap and compare WA class cancellations.
        * mail_manager() - format changes and send them as e-mails.

        Args:
            reset (bool, optional): If True, then delete, then re-create all files from scratch. Defaults to False.
        """
        # file instance
        self.file_manager = FileManager(
            dir_config="./config/",
            dir_work="./work/",
            reset=reset,
        )
        # whether to send e-mails to all participants or not
        self.email_enabled: bool = self.file_manager.config["RUNTIME"]["send_email"]
        # webscraper instances
        self.plan_manager = Plan(self.file_manager)
        self.cancel_manager = Cancel(self.file_manager)
        # mail instance
        self.mail_manager = Mail(self.file_manager)
        return None

    @staticmethod
    def sleep_random(rand_min: int = 2, rand_max: int = 5) -> None:
        """
        Sleep for X seconds.

        Default: random between 1-3 seconds.

        Args:
            rand_min (int, optional): Minimum time to sleep for. Defaults to 2.
            rand_max (int, optional): Maximum time to sleep for. Defaults to 5.
        """
        # generate a random number of seconds to wait for
        wait_time: int = randint(rand_min, rand_max)
        logging.info(f"now waiting for '{wait_time}' seconds to prevent rate-limiting")
        sleep(wait_time)
        return None

    @staticmethod
    def sleep_loop(amount: int = 5) -> None:
        """
        Sleep for X seconds between each loop.

        High values (e.g., 3600) are recommended to avoid redundant frequent checks.

        Args:
            amount (int, optional): Time to sleep for. Defaults to 5.
        """
        logging.info(
            f"now waiting for '{amount}' seconds according to value set in the config file"
        )
        sleep(amount)
        return None

    def get_plan(self) -> None:
        """
        Scrap and compare lesson plan.

        If change found, write to disk and send emails to all recipients.
        If no change found or error, do nothing.
        """
        try:
            # note: running the function on its own will cause the webscrapper to run and write to disk (e.g., is_color_changed())
            # main page's background color
            if self.plan_manager.is_color_changed() and self.email_enabled:
                self.mail_manager.plan_color()
            # link to targeted table
            if self.plan_manager.is_link_changed() and self.email_enabled:
                self.mail_manager.plan_link()
            # content of targeted lesson plan table
            if self.plan_manager.is_table_changed() and self.email_enabled:
                self.mail_manager.plan_table()
        except HTTPError as e:
            # small log
            logging.info(
                f"failed to download lesson plan because the HTTP error was raised ({e})"
            )
        except Timeout as e:
            # small log
            logging.info(
                f"failed to download lesson plan because the maximum timeout for the server to respond was exceed ({e})"
            )
        except ConnectionError as e:
            # small log
            logging.info(
                f"failed to download class cancellations because of connection error (are you online?) ({e})"
            )
        except Exception as e:
            # extremely verbose log
            logging.exception(f"unknown error: lesson plan ({e})")
        finally:
            return None

    def get_cancel(self) -> None:
        """
        Scrap and compare class cancellations.

        If change found, write to disk and send emails to all recipients.
        If no change found or error, do nothing.
        """
        try:
            # class cancellations list
            if self.cancel_manager.is_cancellations_changed() and self.email_enabled:
                self.mail_manager.cancel_content()
        except HTTPError as e:
            # small log
            logging.info(
                f"failed to download class cancellations because the HTTP error was raised ({e})"
            )
        except Timeout as e:
            # small log
            logging.info(
                f"failed to download class cancellations because the maximum timeout for the server to respond was exceed ({e})"
            )
        except ConnectionError as e:
            # small log
            logging.info(
                f"failed to download class cancellations because of connection error (are you online?) ({e})"
            )
        except Exception as e:
            # extremely verbose log
            logging.exception(f"unknown error: class cancellations ({e})")
        finally:
            return None

    def run(self) -> None:
        """
        Run WA webscraper as an infinite blocking loop.

        If 'loop_time_in_seconds' is 0, then quit after 1 loop.
        """
        loop_wait_time: int = self.file_manager.config["RUNTIME"][
            "loop_time_in_seconds"
        ]
        num: int = 0
        while True:
            num += 1
            logging.info(f"running loop no. {num}")
            # scrap lesson plan, write to disk, send emails
            self.get_plan()
            # wait 2-5 seconds to prevent rate-limiting, unless first run of the program (a file was missing)
            if not self.file_manager.first_run:
                self.sleep_random()
            else:
                logging.info("skipping sleep because this is the first run")
            # scrap class cancellations, write to disk, send emails
            self.get_cancel()
            if loop_wait_time == 0:
                logging.info(f"quitting after 1 loop because '{loop_wait_time=}'")
                raise SystemExit  # same as "sys.exit()""
            self.sleep_loop(loop_wait_time)
            logging.info(
                f"ok: running again after having waited for '{loop_wait_time}' seconds"
            )
            # purge all cached variables, so they will be re-downloaded from the web
            self.plan_manager.reset()
            self.cancel_manager.reset()
            continue
        return None


class Debug(App):
    """
    Debug functionality for checking if everything works as it should.
    Example usage:
    >>> debug = Debug()
    >>> debug.mail()
    """

    def __init__(self) -> None:
        # inherit all instances (file, lesson plan, cancel, mail)
        super().__init__(reset=False)
        return None

    def mail(self) -> bool:
        """
        Send debug mail to all targets ("email_receivers") in secret.json.

        Returns:
            bool: True if succeeded, False if failed.
        """
        return self.mail_manager.debug()

    def html(self) -> bool:
        """
        Create HTML file containing current lesson plan table.

        Returns:
            bool: True if succeeded, False if failed.
        """
        html = HtmlManager(file_instance=self.file_manager)
        return html.save()
