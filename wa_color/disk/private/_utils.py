# -*- coding: utf-8 -*-
"""
Extra tools for input and output.
"""
import logging
from json import dump, load
from shutil import rmtree

from . import _templates

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class Directory:
    @staticmethod
    def remove(path: str) -> None:
        """
        Remove a directory recursively.

        If doesn't exist, ignore, if failed, raise.

        Args:
            path (str): Path to directory.
        """
        try:
            rmtree(path)
        except FileNotFoundError:
            logging.debug(f"directory doesn't exists, ignoring '{path}'")
        except Exception as e:
            logging.error(f"failed to remove directory '{path}' ({e})")
            raise
        else:
            logging.debug(f"ok: directory removed '{path}'")
        return None


class Json:
    @staticmethod
    def load_dict(obj) -> dict:
        """
        Load a JSON file as a dictionary (e.g., './data.json').

        If failed, raise.

        Args:
            obj (obj): Path-like object.

        Returns:
            dict: Contents of the file.
        """
        try:
            with obj.open(mode="r", encoding="utf-8") as f:
                r: dict = load(f)
        except OSError as e:
            logging.debug(f"cannot open json file '{obj}' ({e})")
            raise
        except Exception as e:
            logging.debug(f"failed to load json file '{obj}' ({e})")
            raise
        else:
            logging.debug(f"ok: loaded json file '{obj}'")
            return r

    @staticmethod
    def save_dict(obj, value: dict) -> None:
        """
        Save dictionary as a JSON file (e.g., './data.json').

        If failed, raise.

        Args:
            obj (obj): Path-like object.
            value (dict): Contents to be written.

        Returns:
            _type_: None
        """
        try:
            with obj.open(mode="w", encoding="utf-8") as f:
                dump(value, f, indent=4, sort_keys=True, ensure_ascii=False)
        except OSError as e:
            logging.error(f"cannot open json file '{obj}' ({e})")
            raise
        except TypeError as e:
            logging.error(
                f"failed to save json because of type provided, '{obj}' ({e})"
            )
            raise
        except Exception as e:
            logging.error(f"failed to save json '{obj}' ({e})")
            raise
        else:
            logging.debug(f"ok: saved json file '{obj}'")
            return None


class SaveByType:
    @staticmethod
    def html(obj, value: str) -> None:
        """
        Save string containing lesson plan as a HTML table.

        If failed, raise.

        Args:
            obj (obj): Path-like object.
            value (dict): Contents to be written.
        """
        try:
            with obj.open(mode="w", encoding="utf-8") as f:
                f.write(value)
        except Exception as e:
            logging.debug(f"failed to save html file '{obj}' ({e})")
            raise
        else:
            logging.debug(f"ok: saved html file '{obj}'")
            return None


class LoadByType:
    @staticmethod
    def config(path: str) -> dict:
        """
        Return dictionary containing user-defined config file.

        If failed or malformed, create file and return default values.

        Args:
            path (str): Filepath to load file from.

        Returns:
            dict: Contents of the file.
        """
        # prepare default empty template file
        config_default: dict = _templates.config()
        # try to load config file from disk
        try:
            # load from disk
            config: dict = Json.load_dict(obj=path)
            # compare if keys match (naive but better than nothing i guess?)
            if config_default.keys() != config.keys():
                raise IOError("config file's keys do not match placeholder's keys")
        except Exception as e:
            # if failed, write default config
            logging.warning(
                f"failed to load config file '{path}' ({e}), writing default values"
            )
            # overwrite with default placeholder
            config = config_default
            try:
                Json.save_dict(obj=path, value=config)
            except Exception as e:
                logging.warning(
                    f"failed to write default config file '{path}' ({e}), ignoring and returning default values"
                )
            else:
                # if written default values
                logging.debug(
                    f"ok: written default values to config file '{path}', returning default values"
                )
        else:
            # if succeeded loading on 1st try
            logging.debug(f"ok: loaded config file '{path}'")
        return config

    @staticmethod
    def secret(path: str) -> dict:
        """
        Return dictionary containing user-defined sensitive data.

        If failed or malformed, create file and return default values.

        Args:
            path (str): Filepath to load file from.

        Returns:
            dict: Contents of the file.
        """
        # prepare default empty template file
        secret_default: dict = _templates.secret()
        # try to load secret file from disk
        try:
            # load from disk
            secret: dict = Json.load_dict(obj=path)
            # compare if keys match (naive but better than nothing i guess?)
            if secret_default.keys() != secret.keys():
                raise IOError("secret file's keys do not match placeholder's keys")
        except Exception as e:
            # if failed, write default secret
            logging.warning(
                f"failed to load secret file '{path}' ({e}), writing default values"
            )
            # overwrite with default placeholder
            secret = secret_default
            try:
                Json.save_dict(obj=path, value=secret)
            except Exception as e:
                logging.warning(
                    f"failed to write default secret file '{path}' ({e}), ignoring and returning default values"
                )
            else:
                # if written default values
                logging.debug(
                    f"ok: written default values to secret file '{path}', returning default values"
                )
        else:
            # if succeeded loading on 1st try
            logging.debug(f"ok: loaded secret file '{path}'")
        return secret

    @staticmethod
    def plan(path: str) -> dict:
        """
        Return dictionary containing program-defined lesson plan data.

        If failed or malformed, create file and return default values.

        Args:
            path (str): Filepath to load file from.

        Returns:
            dict: Contents of the file.
        """
        # prepare default empty template file
        plan_default: dict = _templates.plan()
        # try to load plan file from disk
        try:
            # load from disk
            plan: dict = Json.load_dict(obj=path)
            # compare if keys match (naive but better than nothing i guess?)
            if plan_default.keys() != plan.keys():
                raise IOError("plan file's keys do not match placeholder's keys")
        except Exception as e:
            # if failed, write default plan
            logging.warning(
                f"failed to load plan file '{path}' ({e}), writing default values"
            )
            # overwrite with default placeholder
            plan = plan_default
            try:
                Json.save_dict(obj=path, value=plan)
            except Exception as e:
                logging.warning(
                    f"failed to write default plan file '{path}' ({e}), ignoring and returning default values"
                )
            else:
                # if written default values
                logging.debug(
                    f"ok: written default values to plan file '{path}', returning default values"
                )
        else:
            # if succeeded loading on 1st try
            logging.debug(f"ok: loaded plan file '{path}'")
        return plan

    @staticmethod
    def cancel(path: str) -> dict:
        """
        Return dictionary containing program-defined class cancellations data.

        If failed or malformed, create file and return default values.

        Args:
            path (str): Filepath to load file from.

        Returns:
            dict: Contents of the file.
        """
        # prepare default empty template file
        cancel_default: dict = _templates.cancel()
        # try to load cancel file from disk
        try:
            # load from disk
            cancel: dict = Json.load_dict(obj=path)
            # compare if keys match (naive but better than nothing i guess?)
            if cancel_default.keys() != cancel.keys():
                raise IOError("cancel file's keys do not match placeholder's keys")
        except Exception as e:
            # if failed, write default cancel
            logging.warning(
                f"failed to load cancel file '{path}' ({e}), writing default values"
            )
            # overwrite with default placeholder
            cancel = cancel_default
            try:
                Json.save_dict(path, value=cancel)
            except Exception as e:
                logging.warning(
                    f"failed to write default cancel file '{path}' ({e}), ignoring and returning default values"
                )
            else:
                # if written default values
                logging.debug(
                    f"ok: written default values to cancel file '{path}', returning default values"
                )
        else:
            # if succeeded loading on 1st try
            logging.debug(f"ok: loaded cancel file '{path}'")
        return cancel
