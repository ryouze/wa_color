# -*- coding: utf-8 -*-
"""
Send e-mail messages based on type, with any changes being automatically detected.
"""
import logging
from email.message import EmailMessage
from platform import python_version, system
from smtplib import SMTP_SSL
from ssl import create_default_context

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class Mail:
    # footer appended at the end of every message, same for every instance
    footer: str = f"sent from {system().lower()} running python {python_version()}\nsource code: https://github.com/ryouze/wa_color/"

    def __init__(self, file_instance) -> None:
        """
        Send e-mails based on type.

        Any changes are detected and formatted automatically.

        Args:
            file_instance (obj): An instance of the File Manager class that accesses JSON files from disk (or RAM, it's automatic).
        """
        # file instance
        self.file_instance = file_instance
        self.timeout: int = 30
        # cached variables
        self.plan_to_send: list = list()
        return None

    def send_mail_api(
        self,
        subject: str,
        message: str,
    ) -> bool:
        """
        Send plain-text e-mail messages to all receivers.

        -> Return True if succeeded.
        -> Return False if failed (no raise).

        Args:
            subject (str): Subject/title of the message, ought to be short.
            message (str): Actual message in plain text.

        Returns:
            bool: True if succeeded, False if failed.
        """
        has_succeeded: bool = False
        try:
            secret = self.file_instance.secret
            # if user hasn't changed default sender, do not even try to send any e-mails
            default_sender: str = "name.surname@example.mail.com"
            if secret["email_sender"]["username"] == "name.surname@example.mail.com":
                logging.debug(
                    f"will not send e-mails because the user hasn't changed the default sender e-mail '{default_sender}' in user.json, ignoring"
                )
                raise Exception(
                    "default sender e-mail in user config hasn't been changed yet"
                )
            # sender's details
            sender_email: str = secret["email_sender"]["username"]  # name@example.com
            password: str = secret["email_sender"]["password"]  # 123abc
            port: int = secret["email_sender"]["port"]  # 465
            smtp_server: str = secret["email_sender"]["server"]  # mail.example.com
            # list of receivers
            receiver_emails: list = secret["email_receivers"]  # ["jeff@mail.com"]
        except Exception as e:
            logging.warning(
                f"failed to setup e-mail variables ({e}), e-mails will not be sent"
            )
        else:
            logging.debug(
                f"trying to log into the sender's e-mail account '{sender_email}' (server={smtp_server}; port={port})"
            )
            try:
                context = create_default_context()
                with SMTP_SSL(
                    smtp_server,
                    port,
                    context=context,
                    timeout=self.timeout,
                ) as server:
                    server.login(sender_email, password)
                    logging.debug(
                        f"ok: logged into '{sender_email}', now trying to send e-mails to '{receiver_emails}'"
                    )
                    # for each receiver, create a formatted email and send it
                    for target in receiver_emails:
                        email = EmailMessage()
                        email["Subject"] = subject
                        email["From"] = sender_email
                        email["To"] = target
                        message += self.footer
                        email.set_content(message)
                        logging.debug(f"trying to send e-mail to '{target}'")
                        server.send_message(email)
                        logging.info(f"ok: sent e-mail message to '{target}'")
                        continue
            except Exception as e:
                logging.error(f"failed to send e-mails to '{receiver_emails}' ({e})")
            else:
                logging.debug(f"ok: sent e-mails to '{receiver_emails}'")
                has_succeeded = True
        finally:
            return has_succeeded

    def add_plan_color(self) -> None:
        """
        Append e-mail message for the Lesson Plan's color change.

        Any changes are detected and formatted automatically.
        """
        temp = self.file_instance.plan
        at_time: str = temp["metadata"]["last_change_color"]
        iteration: int = temp["metadata"]["current_iteration"]
        new_color: str = temp["metadata"]["current_color"]
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
            msg: str = f"lesson plan's color has changed to '#{new_color}' at '{at_time}' (iteration: {iteration})"
        else:
            # if history present
            old_color = list(old_colors.values())[-1]
            msg: str = f"lesson plan's color has changed from '#{old_color}' to '#{new_color}' at '{at_time}' (iteration: {iteration})"
            # add entire history of colors
            msg += "\n\nfull colors history:"
            for num, (key, value) in enumerate(old_colors.items(), start=1):
                msg += f"\n* [{num}] {key} - '#{value}'"
                continue
        logging.info(f"appending plan_color e-mail: '{msg}'")
        self.plan_to_send.append(msg)
        return None

    def add_plan_link(self) -> None:
        """
        Append e-mail message for the Lesson Plan's link change.

        Any changes are detected and formatted automatically.
        """
        temp = self.file_instance.plan
        at_time: str = temp["metadata"]["last_change_link"]
        new_link_before_strip: str = temp["metadata"]["current_link"]
        # remove the beginning of the link, so it's easier to read
        to_strip: str = self.file_instance.config["URL"]["plan_base"]
        new_link: str = new_link_before_strip.replace(to_strip, "")
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
            old_link = list(old_links.values())[-1].replace(to_strip, "")
            msg: str = f"lesson plan's link has changed from '{old_link}' to '{new_link}' at '{at_time}'\n\nyou can view it here: {new_link_before_strip}"
            # add entire history of links
            msg += "\n\nfull links history:"
            for num, (key, value) in enumerate(old_links.items(), start=1):
                msg += f"\n* [{num}] {key} - '{value}'"
                continue
        logging.info(f"appending plan_link e-mail: '{msg}'")
        self.plan_to_send.append(msg)
        return None

    def add_plan_table(self) -> None:
        """
        Send e-mail message for the Lesson Plan's table change.

        Any changes are detected and formatted automatically.
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
        logging.info(f"appending plan table e-mail: '{msg}'")
        self.plan_to_send.append(msg)
        return None

    def send_plan_email(self) -> bool:
        """
        Send e-mail message for the lesson plan's change.

        Any changes are detected and formatted automatically.

        Returns:
            bool: True if succeeded, False if failed.
        """
        if not self.plan_to_send:
            logging.debug("not sending plan email because 'plan_to_send' is empty")
            return False
        msg: str = str()
        for num, content in enumerate(self.plan_to_send, start=1):
            msg += f"{num}. {content}\n\n---\n\n"
            continue
        # the iteration should be in sync because they change the color whenever they change literally anything
        iteration: bool = self.file_instance.plan["metadata"]["current_iteration"]
        mail_status: bool = self.send_mail_api(
            subject=f"wa_color: lesson plan has changed ({iteration})",
            message=msg,
        )
        if not mail_status:
            logging.warning("failed to send e-mails for lesson plan change, ignoring")
        # reset content
        self.plan_to_send: list = list()
        return mail_status

    def send_cancel_email(self) -> bool:
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
        msg: str = f"class cancellation have changed at '{at_time}' (iteration: {iteration})\n\nnew entries only:"
        # find new keys in new_cancel (values are ignored)
        difference = {k: new_cancel[k] for k in set(new_cancel) - set(old_cancel)}
        # sort reverse alphabetically (newest to oldest)
        difference: dict = dict(
            sorted(difference.items(), key=lambda x: x, reverse=True)
        )
        if not difference:
            logging.error(
                f"no difference in keys was found between old cancel '{old_cancel}' and new cancel '{new_cancel}', ignoring"
            )
            return False
        # add new entries
        for num, (key, value) in enumerate(difference.items(), start=1):
            msg += f"\n* [{num}] {key} - '{value}'"
        link: str = self.file_instance.config["URL"]["cancel"]
        msg += f"\n\nyou can view them here: {link}"
        # add entire list
        msg += "\n\nfull class cancellations history:"
        for num, (key, value) in enumerate(new_cancel.items(), start=1):
            msg += f"\n* [{num}] {key} - '{value}'"
        msg += "\n\n---\n\n"  # spacing for footer
        logging.info(f"sending cancel_content e-mail: '{msg}'")
        mail_status: bool = self.send_mail_api(
            subject=f"wa_color: class cancellations have changed ({iteration})",
            message=msg,
        )
        if not mail_status:
            logging.warning(
                "failed to send e-mails for class cancellations change, ignoring"
            )
        return mail_status

    def debug(self) -> bool:
        """
        Send debug e-mail message to see if everything (e.g., passwords) was setup correctly.

        This does not really on any JSON files.

        Returns:
            bool: True if succeeded, False if failed.
        """
        msg: str = "this is a debug message to see if everything works"
        logging.info(f"sending debug e-mail: '{msg}'")
        mail_status: bool = self.send_mail_api(
            subject="wa_color: debug message",
            message=msg,
        )
        if not mail_status:
            logging.warning("failed to send e-mails for debug message, ignoring")
        return mail_status
