# -*- coding: utf-8 -*-
"""
Load and save files on-demand: config, plan, cancel, html.
Example usage:
>>> f = File(reset=False)
>>> f.plan = {"iteration": 20}
"""
import logging
from pathlib import Path

from .private._utils import Directory, Json, LoadByType, SaveByType

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class FileManager:
    def __init__(
        self,
        dir_config: str = "./config/",
        dir_work: str = "./work/",
        path_html: str = "./output.html",
        reset: bool = False,
        absolute_path: bool = True,
    ) -> None:
        """
        Create directories (config, work) and files (config, secret, lesson plan, class cancellations, WA news, HTML table).

        If failed, raise.
        If any of the directories/files missing, write placeholders (JSON) to disk and load to cache.
            Since we have to create all JSON files anyway, we might as well cache them at once.

        Args:
            dir_config (str, optional): Directory for user-defined config files. Defaults to "./config/".
            dir_work (str, optional): Directory for program-defined data files. Defaults to "./work/".
            path_html (str, optional): Path to HTML table (NOT created by default). Defaults to "./output.html".
            reset (bool, optional): If True, then delete, then re-create all files from scratch. Defaults to False.
            absolute_path (bool, optional): Convert relative filepaths to absolute paths. Defaults to True.
        """
        self.first_run: bool = False
        try:
            # define filepaths to directories (to be discarded)
            dir_config = Path(dir_config).resolve()
            dir_work = Path(dir_work).resolve()
            self._filepath_html = Path(path_html).resolve()
            # get absolute filepath (enabled by default)
            if absolute_path:
                dir_config = dir_config.resolve()
                dir_work = dir_work.resolve()
            # create directories
            for obj in [dir_config, dir_work]:
                if reset:
                    Directory.remove(obj)
                    logging.debug(f"ok: removed directory '{obj}'")
                # ignore if already exists
                if obj.is_dir():
                    logging.debug(f"ok: directory already exists '{obj}', ignoring")
                    continue
                obj.mkdir(parents=True, exist_ok=False)
                self.first_run = True  # cache all files
                logging.debug(f"ok: created directory '{obj}'")
                continue
        except Exception as e:
            logging.error(f"could not create directories ({e})")
            raise
        try:
            # define filepaths to files (to be kept)
            self._filepath_config = Path(dir_config, "user.json")
            self._filepath_secret = Path(dir_config, "secret.json")
            self._filepath_plan = Path(dir_work, "plan.json")
            self._filepath_cancel = Path(dir_work, "cancel.json")
            # create files
            for obj in [
                self._filepath_config,
                self._filepath_secret,
                self._filepath_plan,
                self._filepath_cancel,
            ]:
                # ignore if already exists
                if obj.is_file():
                    logging.debug(f"ok: file already exists '{obj}', ignoring")
                    continue
                obj.touch(exist_ok=False)
                self.first_run = True  # cache all files
                logging.debug(f"ok: created file '{obj}'")
        except Exception as e:
            logging.error(f"could not create files ({e})")
            raise
        # cached variables, will be loaded only if requested
        if self.first_run:
            # if first run then use LoadByType to create default placeholder files
            logging.debug("first run, creating and caching all JSON files at once")
            self._config: dict = LoadByType.config(self._filepath_config)
            self._secret: dict = LoadByType.secret(self._filepath_secret)
            self._plan: dict = LoadByType.plan(self._filepath_plan)
            self._cancel: dict = LoadByType.cancel(self._filepath_cancel)
            logging.debug("ok: files were loaded and cached")
        else:
            logging.debug("not first run, loading JSON files on-demand")
            self._config: dict = dict()
            self._secret: dict = dict()
            self._plan: dict = dict()
            self._cancel: dict = dict()
        return None

    @property
    def config(self) -> dict:
        """
        Load config file - if cache unavailable, load from disk, if cache available, load from RAM.
        If failed, create file and return default values.

        Returns:
            dict: Contents of the file.
        """
        logging.debug("GET: CONFIG (try to load from cache, then from disk)")
        if not self._config:
            logging.debug(f"config not cached, loading now '{self._filepath_config}'")
            self._config = LoadByType.config(self._filepath_config)
        else:
            logging.debug("ok: config was cached, returning from RAM")
        return self._config

    @property
    def secret(self) -> dict:
        """
        Load secret file - if cache unavailable, load from disk, if cache available, load from RAM.
        If failed, create file and return default values.

        Returns:
            dict: Contents of the file.
        """
        logging.debug("GET: SECRET (try to load from cache, then from disk)")
        if not self._secret:
            logging.debug(f"secret not cached, loading now '{self._filepath_secret}'")
            self._secret = LoadByType.secret(self._filepath_secret)
        else:
            logging.debug("ok: secret was cached, returning from RAM")
        return self._secret

    @property
    def plan(self) -> dict:
        """
        Load lesson plan file - if cache unavailable, load from disk, if cache available, load from RAM.
        If failed, create file and return default values.

        Returns:
            dict: Contents of the file.
        """
        logging.debug("GET: PLAN (try to load from cache, then from disk)")
        if not self._plan:
            logging.debug(f"plan not cached, loading now '{self._filepath_plan}'")
            self._plan = LoadByType.plan(self._filepath_plan)
        else:
            logging.debug("ok: plan was cached, returning from RAM")
        return self._plan

    @plan.setter
    def plan(self, content: dict) -> None:
        """
        Save lesson plan file to disk and to RAM.

        Data stored in RAM is used for comparison with data scraped from the internet.

        Args:
            content (dict): Contents to be written.
        """
        logging.debug("SET: PLAN (save to disk & cache)")
        Json.save_dict(obj=self._filepath_plan, value=content)
        self._plan = content
        return None

    @property
    def cancel(self) -> dict:
        """
        Load class cancellations file - if cache unavailable, load from disk, if cache available, load from RAM.
        If failed, create file and return default values.

        Returns:
            dict: Contents of the file.
        """
        logging.debug("GET: CANCEL (try to load from cache, then from disk)")
        if not self._cancel:
            logging.debug(f"cancel not cached, loading now '{self._filepath_cancel}'")
            self._cancel = LoadByType.cancel(self._filepath_cancel)
        else:
            logging.debug("ok: cancel was cached, returning from RAM")
        return self._cancel

    @cancel.setter
    def cancel(self, content: dict) -> None:
        """
        Save class cancellations file to disk and to RAM.

        Data stored in RAM is used for comparison with data scraped from the internet.

        Args:
            content (dict): Contents to be written.
        """
        logging.debug("SET: CANCEL (save to disk & cache)")
        Json.save_dict(obj=self._filepath_cancel, value=content)
        self._cancel = content
        return None

    @property
    def html(self) -> None:
        """
        Unimplemented, no need for reading it right now.

        Raises:
            NotImplementedError: We only need to save the file, so this is a dummy function.
        """
        raise NotImplementedError

    @html.setter
    def html(self, content: dict) -> None:
        """
        Save lesson plan file to disk, do not keep it in RAM.

        This is a HTMl file containing lesson plan, after being ran by HTML function.

        Args:
            content (dict): Contents to be written.
        """
        logging.debug("SET: html (save to disk)")
        SaveByType.html(obj=self._filepath_html, value=content)
        return None
