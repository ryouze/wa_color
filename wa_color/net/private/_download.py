# -*- coding: utf-8 -*-
"""
Download and process webpages: lesson plan, class cancellations.
"""
import logging
import re

from bs4 import BeautifulSoup
from requests import HTTPError, Session

from . import _convert as convert

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class _Shared:
    # cached user agent
    _ua: str = str()
    # try to fetch latest on 1st run or always return default; only set to True if debugging
    bypass_ua_fetch: bool = False

    @classmethod
    def get_user_agent(cls, timeout: int = 16) -> str:
        """
        Fetch cached Chrome user agent.

        On first run, try to fetch latest user agent from 'whatismybrowser.com' and cache it.
        On consecutive run, return cache and never re-attempt to fetch anything.
            This may potentially fail but the WA webpage doesn't seem to block scrapers anyway.
        If failed, return default Chrome user agent (might be outdated) and cache it.

        Args:
            timeout (int, optional): How much time to wait before giving up. Defaults to 16.

        Returns:
            str: Chrome user agent.
        """
        # if already cached, return as-is
        if cls._ua:
            logging.debug(
                f"user_agent is already scraped '{cls._ua}', returning cached"
            )
            return cls._ua
        default_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
        # if bypass enabled, do not attempt to fetch anything
        if cls.bypass_ua_fetch:
            logging.warning(
                "bypass is enabled (disable after debugging), setting default user agent as cache and returning it"
            )
            cls._ua = default_agent
            return cls._ua
        url: str = "https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome"
        try:
            with Session() as s:
                # they might try to block scrapers in the future, so use default user agent
                s.headers.update({"User-Agent": default_agent})
                logging.debug("fetching latest chrome useragent")
                r = s.get(url, timeout=timeout)
                # if not OK response, raise
                r.raise_for_status()
            # convert to bs4 soup object
            soup = convert.soup(r)
            table = soup.find(
                "table", {"class": re.compile(".*listing-of-useragents.*")}
            )
            li = table.find("li")
            span = li.find("span", {"class": "code"})
            scraped_agent: str = span.get_text(strip=True)
            del soup, table, li, span  # delete, unneeded
            # if shorter than 5 characters, raise exception to trigger default user agent
            if len(scraped_agent) < 5:
                raise Exception(
                    f"latest user agent '{scraped_agent}' is shorter than 5 characters, probably malformed"
                )
            # if "mozilla" or "chrome" not present, raise exception to trigger default user agent
            for name in ["mozilla", "chrome"]:
                if name not in scraped_agent.lower():
                    raise Exception(
                        f"latest user agent '{scraped_agent}' does not contain '{name}', probably malformed"
                    )
            logging.info(f"ok: extracted latest user agent '{scraped_agent}'")
            # cache latest user agent
            cls._ua = scraped_agent
        except HTTPError as e:
            logging.warning(
                f"failed to extract latest user agent due to a network issue ({e}), returning default '{default_agent}'"
            )
            # cache default user agent
            cls._ua = default_agent
        except Exception as e:
            logging.warning(
                f"failed to extract latest user agent ({e}), returning default '{default_agent}'"
            )
            # cache default user agent
            cls._ua = default_agent
        return cls._ua

    @staticmethod
    def combine_base_link_and_href(first: str, second: str) -> str:
        """
        Combine base link with href.

        Slashes are added/removed when necessary and index.html is removed.

        Args:
            first (str): Base website link (e.g., 'https://website.com/index.html').
            second (str): Sub page link (e.g., 'file1.html').

        Returns:
            str: Combined link (e.g., 'https://website.com/file1.html').
        """
        # remove "index.html" at the end, with some lee-way
        if "/index.html" in first[-15:]:
            first = first.replace("/index.html", "")
            logging.debug(f"removed trailing '/index.html' from first '{first}'")
        # add trailing slash to second (e.g., "website.com" -> "website.com/")
        if first[-1] != ("/"):
            first += "/"
            logging.debug(f"added missing trailing slash to first '{first}'")
        # remove leading slash from second (e.g., "/file.html")
        if second[0] == "/":
            second = second[1:]
            logging.debug(f"removed extra leading slash from second '{second}'")
        first += second
        logging.debug(f"ok: combined link '{first}'")
        return first


class DownloadPlan:
    def __init__(self, url: str, pattern: str) -> None:
        """
        Setup URL containing the list of groups and regex for specific group (e.g., '3BA Theater').

        If attribute already cached, do not scrap again.
        If reset() is ran, purge cache (will be scraped next time).

        Args:
            url (str): Link containing the list of lesson groups; slashes will be added automatically.
            pattern (str): Regex pattern used to find a specific group (e.g., '3.*ter').
        """
        self._url: str = url
        self._pattern: str = pattern
        # cached variables, will be loaded only if requested
        self._downloaded_main_page: BeautifulSoup = None
        self._sub_link: str = str()
        self._downloaded_sub_page: BeautifulSoup = None
        self._main_color: str = str()
        self._sub_table: dict = dict()
        return None

    @staticmethod
    def _get_color_from_soup(obj) -> str:
        """
        Get background color from BeautifulSoup object.

        If failed, raise.

        Args:
            obj (BeautifulSoup): Main page soup object.

        Returns:
            str: Hexadecimal color (e.g., CD61B8).
        """
        try:
            style = obj.find("style").get_text()
            matches = re.search("background-color:#(.{6});", style, re.IGNORECASE)
            # group 0 = includes entire pattern with match (e.g., 'time=30')
            # group 1 = includes match only (e.g., '30')
            color: str = matches.group(1)
        except Exception as e:
            logging.error(f"could not find background color ({e})")
            raise
        else:
            logging.debug(f"ok: found background color '{color}'")
            return color

    @staticmethod
    def _get_href_by_regex_from_soup(obj, pattern: str) -> str:
        """
        Get href link to target group.

        E.g., link '/o1.html' is found using regex '3.*Dutch'.
        If failed, raise.

        Args:
            (BeautifulSoup): Sub page soup object.
            pattern (str): Regex pattern used to find specific group (e.g., '3.*Dutch').

        Returns:
            str: href for target group (e.g., '/o1.html').
        """
        try:
            table = obj.find("table")
            # extract all links
            for tr in table.find_all("td"):
                a = tr.find("a")
                # logging.debug(f"checking link '{a}'")
                # if link's text matches the group (e.g., 3BA.*Dutch), return it
                if re.match(pattern, a.text, re.IGNORECASE):
                    href: str = a["href"]
                    logging.debug(f"found target href '{href}'")
                    return href
            # otherwise, raise
            raise Exception("checked all groups, none matched regex pattern")
        except Exception as e:
            logging.error(f"could not find sublink using '{pattern}' ({e})")
            raise

    @staticmethod
    def _get_table_from_soup(obj) -> dict:
        """
        Get dictionary representation of targeted lesson plan table.

        Key = day, value list = lessons.
            E.g., {"monday": ["IT CLASS", "", "ONLINE CLASS"]}
        If failed, raise.

        Args:
            (BeautifulSoup): Sub page soup object.

        Returns:
            dict: Representation of lesson plan table.
        """
        try:
            table = obj.find("table")
            r: dict = {
                "time": list(),
                "monday": list(),
                "tuesday": list(),
                "wednesday": list(),
                "thursday": list(),
                "friday": list(),
            }
            # for each row (vertical, e.g., 08:00, 09:45, 11:30)
            for tr_num, tr in enumerate(table.find_all("tr")):
                # if first cell (title), ignore (e.g., Monday, Tuesday)
                if tr_num == 0:
                    logging.debug(
                        "skipping first cell containing day (e.g., Monday, Tuesday)"
                    )  #'{tr}'")
                    continue
                # for each cell (horizontal, e.g., Monday, Tuesday, Wednesday)
                # list for entire row (horizontal)
                data: list = list()
                for td_num, td in enumerate(tr.find_all("td")):
                    try:
                        # convert <br> to newlines
                        text = td.get_text(separator="\n", strip=True)
                    except Exception as e:
                        logging.error(f"failed to extract text from '{td}' ({e})")
                        raise
                    else:
                        # if first cell (hour), replace dot with colon (e.g., '12.30' -> '12:30')
                        if td_num == 0:
                            text = text.replace(".", ":")
                            # if hour is single digit, append "0" in front (e.g., '9:45' -> '09:45')
                            if len(text.split(":")[0]) == 1:
                                text = "0" + text
                            # logging.debug(
                            #     f"converted hour to military time with colon '{text}'"
                            # )
                        data.append(text)
                        continue
                # if data (horizontally) doesn't have 6 items (hour + 5 days in a week), then raise
                if len(data) != 6:
                    raise Exception(
                        "table row doesn't have 6 items (hour + 5 days in a week)"
                    )
                # add to dictionary (day = list of lessons)
                for num, key in enumerate(r):
                    r[key].append(data[num])
                    continue
                continue
            logging.debug("ok: scraped table")
            return r
        except Exception as e:
            logging.error(f"could not extract data from table ({e})")
            raise

    def _download_pages(self, timeout: int = 16) -> None:
        """
        Download two webpages: main and sub page containing table.

        Cache main (bs4 obj), link to sub page (str) and sub page (bs4 obj).
        If failed, raise.

        Args:
            timeout (int, optional): How much time to wait before giving up. Defaults to 16.
        """
        if self._downloaded_main_page and self._downloaded_sub_page:
            logging.debug("pages already downloaded")
            return None
        try:
            with Session() as s:
                # set chrome header to avoid bot detection (as if they blocked bots to begin with)
                s.headers.update({"User-Agent": _Shared.get_user_agent()})
                # download main page and convert to bs4 object
                main_page = s.get(self._url, timeout=timeout)
                main_page.raise_for_status()  # if not OK response, raise
                self._downloaded_main_page = convert.soup(main_page)
                logging.debug(
                    f"ok: downloaded main lesson plan page containing list of groups '{self._url}'"
                )
                # find link to table using regex within main page
                href: str = self._get_href_by_regex_from_soup(
                    obj=self._downloaded_main_page, pattern=self._pattern
                )
                # combine base link with href
                self._sub_link = _Shared.combine_base_link_and_href(
                    first=self._url, second=href
                )
                logging.debug(
                    f"ok: found link to subpage using regex '{self._sub_link}'"
                )
                # use combined link to download sub page and convert to bs4 object
                sub_page = s.get(self._sub_link, timeout=timeout)
                sub_page.raise_for_status()  # if not OK response, raise
                self._downloaded_sub_page = convert.soup(sub_page)
                logging.debug(f"ok: downloaded subpage containing table '{self._url}'")
        except HTTPError as e:
            logging.error(
                f"failed to download two lesson plan webpages (main & table) due to a network issue ({e})"
            )
            raise
        except Exception as e:
            logging.error(
                f"couldn't download two lesson plan webpages (main & table) ({e})"
            )
            raise
        else:
            return None

    @property
    def color(self) -> str:
        """
        Get plan page's background color string.

        If cache unavailable, find using regex.
        If failed, raise.

        Returns:
            str: Hexadecimal color (e.g., CD61B8).
        """
        logging.debug("GET: COLOR (try to load from cache, then from internet)")
        if not self._main_color:
            logging.debug("color not cached, scraping now")
            # if main page obj not available, download it
            if not self._downloaded_main_page:
                logging.debug("main page not cached, downloading both now")
                self._download_pages()
            self._main_color = self._get_color_from_soup(obj=self._downloaded_main_page)
        else:
            logging.debug("ok: color was cached, returning from RAM")
        return self._main_color

    @property
    def link(self) -> str:
        """
        Return cached link string to sub page containing table.

        If cache unavailable, download both webpages and find link.
        If failed, raise.

        Returns:
            str: Link to targeted lesson plan table (e.g., "website/groups/o99.html').
        """
        logging.debug("GET: LINK (try to load from cache, then from internet)")
        if not self._sub_link:
            logging.debug("link not cached, scraping now")
            # if main page obj not available, download it
            if not self._downloaded_main_page:
                logging.debug("main page not cached, downloading both now")
                self._download_pages()
            # _download_pages() will cache sublink as well because it's required to find subpage anyway
        else:
            logging.debug("ok: link was cached, returning from RAM")
        return self._sub_link

    @property
    def table(self) -> dict:
        """
        Get cached table dictionary inside sub page that contains group's lesson plan.

        Key = day, value list = lessons.
            E.g., {"monday": ["IT CLASS", "", "ONLINE CLASS"]}
        If cache unavailable, download both webpages and scrap table.
        If failed, raise.

        Returns:
            dict: Representation of lesson plan table.
        """
        logging.debug("GET: TABLE (try to load from cache, then from internet)")
        if not self._sub_table:
            logging.debug(f"table not cached '{self._main_color}', scraping now")
            # if sub page obj not available, download it
            if not self._downloaded_sub_page:
                logging.debug(
                    f"subpage not cached '{self._main_color}', downloading both now"
                )
                self._download_pages()
            self._sub_table = self._get_table_from_soup(obj=self._downloaded_sub_page)
        else:
            logging.debug("ok: table was cached, returning from RAM")
        return self._sub_table

    def reset(self) -> None:
        """
        Purge all cached variables.

        This will cause the web scrapper to download and process webpages again.
        """
        self._downloaded_main_page = None
        self._sub_link = str()
        self._downloaded_sub_page = None
        self._main_color = str()
        self._sub_table = dict()
        logging.debug("ok: lesson plan cache purged, waiting for next loop")
        return None


class DownloadCancel:
    def __init__(self, url: str) -> None:
        """
        Setup URL containing the list of class cancellations.

        If attribute already cached, do not scrap again.
        If reset() is ran, purge cache (will be scraped next time).

        Args:
            url (str): Link containing the list of class cancellations; slashes will be added automatically.
        """
        self._url: str = url
        # cached variables, will be loaded only if requested
        self._downloaded_page: BeautifulSoup = None
        self._cancellations: dict = dict()
        return None

    def _download_page(self, timeout: int = 16) -> None:
        """
        Download webpage: list of class cancellations.

        Cache webpage (bs4 obj).
        If failed, raise.

        Args:
            timeout (int, optional): How much time to wait before giving up. Defaults to 16.
        """
        if self._downloaded_page:
            logging.debug("page already downloaded")
            return None
        try:
            with Session() as s:
                # set chrome header to avoid bot detection (as if they blocked bots to begin with)
                s.headers.update({"User-Agent": _Shared.get_user_agent()})
                # download page and convert to bs4 object
                page = s.get(self._url, timeout=timeout)
                page.raise_for_status()  # if not OK response, raise
                self._downloaded_page = convert.soup(page)
                logging.debug(
                    f"ok: downloaded page containing list of class cancellations '{self._url}'"
                )
        except HTTPError as e:
            logging.error(
                f"failed to download class cancellation webpage due to a network issue ({e})"
            )
            raise
        except Exception as e:
            logging.error(f"could not download class cancellation webpage ({e})")
            raise
        else:
            return None

    def _get_cancellations_from_soup(self) -> dict:
        """
        Get dictionary representation of class cancellations.

        Key = date, value = individual class cancellation string.
            E.g., {'2022-09-08': 'XYZ cancels their classes'}
        If failed, raise.

        Args:
            (BeautifulSoup): Soup object.

        Returns:
            dict: Representation of class cancellations list.
        """
        if not self._downloaded_page:
            logging.debug("page not cached, downloading now")
            self._download_page()
        try:
            proper_content = self._downloaded_page.find("div", id="tresc_wlasciwa")
            r: dict = dict()
            li_pattern = re.compile("views-row views-row-.*")
            for li in proper_content.find_all("li", class_=li_pattern):
                try:
                    title: str = li.find("a").get_text(strip=True).rstrip(".")
                    date: str = li.find_all("span")[1].get_text(strip=True)
                except Exception as e:
                    logging.warning(
                        f"failed to extract a single piece of cancellations from '{li}' ({e}), ignoring"
                    )
                    continue
                else:
                    r.update({date: title})
                    # logging.debug(f"found cancellations: '{title}'")
                    continue
        except Exception as e:
            logging.error(f"could not extract class cancellations from page ({e})")
            raise
        else:
            return r

    @property
    def cancellations(self) -> dict:
        """
        Get list of class cancellations.

        If cache unavailable, find class cancellations.
        If failed, raise.

        Returns:
            dict: Representation of class cancellations list.
        """
        logging.debug("GET: CANCELLATIONS (try to load from cache, then from internet)")
        if not self._cancellations:
            logging.debug("cancellations not cached, scraping now")
            self._cancellations = self._get_cancellations_from_soup()
        else:
            logging.debug("ok: cancellations were cached, returning from RAM")
        return self._cancellations

    def reset(self) -> None:
        """
        Purge all cached variables.

        This will cause the web scrapper to download and process webpages again.
        """
        self._downloaded_page = None
        self._cancellations = list()
        logging.debug("ok: class cancellations cache purged, waiting for next loop")
        return None
