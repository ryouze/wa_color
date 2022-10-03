# -*- coding: utf-8 -*-
"""
Main entry: setup rotating logger and run app.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

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
    # check for cli arguments (e.g., 'main.py --mail')
    reset: bool = False
    if len(sys.argv) > 1:
        first_arg: str = sys.argv[1]
        logging.getLogger().setLevel(logging.DEBUG)
        if first_arg == "--verbose":
            # run webscraper normally
            logging.info("found arg: '--verbose', using verbose DEBUG-level logging")
        elif first_arg == "--reset":
            # run webscraper normally, but re-create all directories from scratch first
            # this also sets 'loop_wait_time' to 0, so it will quit after first loop
            logging.info(
                "found arg: '--reset', re-creating all directories from scratch"
            )
            reset = True
        elif first_arg == "--mail":
            # send debug e-mail, then quit without running webscraper
            logging.info("found arg: '--mail', sending debug e-mail now")
            debug = Debug()
            r = debug.mail()
            logging.info(f"mail success status: {r}")
            return None
        elif first_arg == "--html":
            # send create html file from lesson plan, then quit without running webscraper
            logging.info("found arg: '--html', creating html file now")
            debug = Debug()
            r = debug.html()
            logging.info(f"html success status: {r}")
            return None
        else:
            logging.error(f"unknown cli argument: '{sys.argv[1]}', quitting")
            return None
    else:
        logging.debug("ok: no cli argument provided")
    # run webscraper as an infinite loop (unless 'loop_wait_time' is set to 0)
    app = App(reset=reset)
    app.run()
    return None


if __name__ == "__main__":
    main()
