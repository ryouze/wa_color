# -*- coding: utf-8 -*-
"""
Main entry: setup rotating logger and run app.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser

from wa_color.main import App, Debug


def main() -> None:
    """
    The main entry point to the application.

    Example usage:
    >>> python3 main.py
    >>> python3 main.py --reset
    >>> python3 main.py --mail
    >>> python3 main.py --html
    """
    # setup logger
    logging.basicConfig(
        datefmt="%G-%m-%d %T",
        format="%(asctime)s [%(levelname)s] %(filename)s : %(funcName)s() (%(lineno)d) - %(message)s",
        handlers=[
            # write to file, rotate after at least 2,500 lines
            RotatingFileHandler(
                "./app.log", maxBytes=350_000, backupCount=5, encoding="utf-8"
            ),
            # write to console
            logging.StreamHandler(sys.stdout),
        ],
        level=logging.INFO,
    )
    # process CLI arguments (e.g., 'main.py --mail')
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        help="flag: enable verbose, debug-level logging",
        action="store_true",  # doesn't take value, returns true if provided, otherwise false
    )
    parser.add_argument(
        "--reset",
        help="flag: destroy all data, equivalent to running the program for the first time",
        action="store_true",  # doesn't take value, returns true if provided, otherwise false
    )
    parser.add_argument(
        "--html",
        help="flag: create html table based on the lesson plan, then quit",
        action="store_true",  # doesn't take value, returns true if provided, otherwise false
    )
    parser.add_argument(
        "--mail",
        help="flag: send debug e-mail to all recipients, then quit",
        action="store_true",  # doesn't take value, returns true if provided, otherwise false
    )
    args = parser.parse_args()
    reset: bool = False
    if args.verbose:
        logging.info("found arg 'verbose' - enable verbose, debug-level logging")
        logging.getLogger().setLevel(logging.DEBUG)
    if args.reset:
        # run webscraper normally, but re-create all directories from scratch first
        # this also sets 'loop_wait_time' to 0, so it will quit after first loop
        logging.info(
            "found arg 'reset' - destroy all data, equivalent to running the program for the first time"
        )
        reset = True
    if args.html:
        # create html file from lesson plan, then quit without running webscraper
        logging.info(
            "found arg 'html' - create html table based on the lesson plan, then quit"
        )
        debug = Debug()
        r = debug.html()
        return None
    if args.mail:
        # send debug e-mail, then quit without running webscraper
        logging.info(
            "found arg 'mail' - send debug e-mail to all recipients, then quit"
        )
        debug = Debug()
        r = debug.mail()
        logging.info(f"mail success status: {r}")
        return None
    # run webscraper as an infinite loop (unless 'loop_wait_time' is set to 0)
    app = App(reset=reset)
    app.run()
    return None


if __name__ == "__main__":
    main()
