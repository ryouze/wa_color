# -*- coding: utf-8 -*-
"""
Send e-mail messages based on type, with any changes being automatically detected.
"""
import logging

from .private import mail_api

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class Mail:
    def __init__(self, file_instance) -> None:
        """
        Send e-mails based on type.

        Any changes are detected and formatted automatically.

        Args:
            file_instance (obj): An instance of the File Manager class that accesses JSON files from disk.
        """
        # file instance
        self.file_instance = file_instance
        return None

    def plan_color(self) -> bool:
        """
        Send e-mail message for the Lesson Plan's color change.

        Any changes are detected and formatted automatically.

        Returns:
            bool: True if succeeded, False if failed.
        """
        temp = self.file_instance.plan
        at_time: str = temp["metadata"]["last_change_color"]
        iteration: int = temp["metadata"]["current_iteration"]
        new_color: list = temp["metadata"]["current_color"]
        # sort alphabetically (oldest to newest)
        # note: they're sorted alphabetically in JSON but not in cache, so this is a precaution
        old_colors: dict = dict(
            sorted(
                temp["metadata"]["previous_colors"].items(),
                key=lambda x: x,
                reverse=False,
            )
        )
        del temp  # delete, unneeded
        if not old_colors:
            # if no history
            logging.warning("not appending color history to email because it's empty")
            msg: str = f"lesson plan's color has changed to '{new_color}' at '{at_time}' (iteration: {iteration})"
        else:
            # if history present
            old_color = list(old_colors.values())[-1]
            msg: str = f"lesson plan's color has changed from '{old_color}' to '{new_color}' at '{at_time}' (iteration: {iteration})"
            # add entire history of colors
            msg += "\n\nfull colors history:"
            for num, (key, value) in enumerate(old_colors.items(), start=1):
                msg += f"\n* [{num}] {key} - '{value}'"
                continue
        logging.info(f"sending plan_color e-mail: '{msg}'")
        return mail_api.send(
            secret=self.file_instance.secret,
            subject="wa_color: lesson plan's color has changed",
            message=msg,
        )

    def plan_link(self) -> bool:
        """
        Send e-mail message for the Lesson Plan's link change.

        Any changes are detected and formatted automatically.

        Returns:
            bool: True if succeeded, False if failed.
        """
        temp = self.file_instance.plan
        at_time: str = temp["metadata"]["last_change_link"]
        new_link: list = temp["metadata"]["current_link"].replace(r"https://", "")
        new_link_before_strip: str = temp["metadata"]["current_link"]
        # sort alphabetically (oldest to newest)
        # note: they're sorted alphabetically in JSON but not in cache, so this is a precaution
        old_links: dict = dict(
            sorted(
                temp["metadata"]["previous_links"].items(),
                key=lambda x: x,
                reverse=False,
            )
        )
        del temp  # delete, unneeded
        if not old_links:
            # if no history
            logging.warning("not appending link history to email because it's empty")
            msg: str = f"lesson plan's link has changed to '{new_link}' at '{at_time}'\n\nyou can view it here: {new_link_before_strip}"
        else:
            # if history present
            old_link = list(old_links.values())[-1].replace(r"https://", "")
            msg: str = f"lesson plan's link has changed from '{old_link}' to '{new_link}' at '{at_time}'\n\nyou can view it here: {new_link_before_strip}"
            # add entire history of links
            msg += "\n\nfull links history:"
            for num, (key, value) in enumerate(old_links.items(), start=1):
                msg += f"\n* [{num}] {key} - '{value}'"
                continue
        logging.info(f"sending plan_link e-mail: '{msg}'")
        return mail_api.send(
            secret=self.file_instance.secret,
            subject="wa_color: lesson plan's link has changed",
            message=msg,
        )

    def plan_table(self) -> bool:
        """
        Send e-mail message for the Lesson Plan's table change.

        Any changes are detected and formatted automatically.

        Returns:
            bool: True if succeeded, False if failed.
        """
        temp = self.file_instance.plan
        old_plan: dict = temp["previous"]
        at_time: str = temp["metadata"]["last_change_table"]
        new_plan: dict = temp["current"]
        del temp  # delete, unneeded
        msg: str = (
            f"lesson plan's table has changed at '{at_time}', here are the differences:"
        )
        shared: set = set(old_plan.keys()).intersection(new_plan.keys())
        # find actual changes
        for day in shared:
            for hour, old_subj, new_subj in zip(
                new_plan["time"], old_plan[day], new_plan[day]
            ):
                # if subject at a given day and time slot is different, append
                if old_subj != new_subj:
                    # replace newlines with semicolons
                    old_subj = old_subj.replace("\n", "; ")
                    new_subj = new_subj.replace("\n", "; ")
                    # append positional data
                    msg += f"\n* [{day} @ {hour}] '{old_subj}' --> '{new_subj}'"
        logging.info(f"sending plan_table e-mail: '{msg}'")
        return mail_api.send(
            secret=self.file_instance.secret,
            subject="wa_color: lesson plan's table has changed",
            message=msg,
        )

    def cancel_content(self) -> bool:
        """
        Send e-mail message for the class cancellations's content change.

        Any changes are detected and formatted automatically.

        Returns:
            bool: True if succeeded, False if failed.
        """
        temp = self.file_instance.cancel
        at_time: str = temp["metadata"]["last_change"]
        iteration: int = temp["metadata"]["current_iteration"]
        # sort alphabetically (newest to oldest)
        # note: they're sorted alphabetically in JSON but not in cache, so this is a precaution
        old_cancel: dict = dict(
            sorted(temp["previous"].items(), key=lambda x: x, reverse=True)
        )
        new_cancel: dict = dict(
            sorted(temp["current"].items(), key=lambda x: x, reverse=True)
        )
        del temp  # delete, unneeded
        msg: str = f"class cancellation has changed at '{at_time}' (iteration: {iteration})\n\nnew entries only:"
        # find new keys in new_cancel (values are ignored)
        difference = {k: new_cancel[k] for k in set(new_cancel) - set(old_cancel)}
        # sort reverse alphabetically (newest to oldest)
        difference: dict = dict(
            sorted(difference.items(), key=lambda x: x, reverse=True)
        )
        if not difference:
            logging.warning(
                f"no difference in keys was found between old cancel '{old_cancel}' and new cancel '{new_cancel}', ignoring"
            )
            return False
        # add new entries
        for num, (key, value) in enumerate(difference.items(), start=1):
            msg += f"\n* [{num}] {key} - '{value}'"
        # add entire list
        msg += "\n\nall class cancellations:"
        for num, (key, value) in enumerate(new_cancel.items(), start=1):
            msg += f"\n* [{num}] {key} - '{value}'"
        logging.info(f"sending cancel_content e-mail: '{msg}'")
        return mail_api.send(
            secret=self.file_instance.secret,
            subject="wa_color: class cancellations has changed",
            message=msg,
        )

    def debug(self) -> bool:
        """
        Send debug e-mail message to see if everything (e.g., passwords) was setup correctly.

        This does not really on any JSON files.

        Returns:
            bool: True if succeeded, False if failed.
        """
        msg: str = "this is a debug message to see if everything works"
        logging.info(f"sending debug e-mail: '{msg}'")
        return mail_api.send(
            secret=self.file_instance.secret,
            subject="wa_color: debug message",
            message=msg,
        )
