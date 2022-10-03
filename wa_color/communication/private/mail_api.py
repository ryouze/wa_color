# -*- coding: utf-8 -*-
"""
API for sending e-mail messages.
"""
import logging
from smtplib import SMTP_SSL
from ssl import create_default_context

from ._formatting import FormattedEmail

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class MailAPI:
    @staticmethod
    def send(
        secret: dict,
        subject: str,
        message: str,
        timeout: int = 30,
    ) -> bool:
        """
        Try to send plain-text e-mail messages to all receivers.

        -> Return True if succeeded.
        -> Return False if failed (no raise).

        Args:
            secret (dict): Dictionary containing username, passwords, receivers, etc.
            subject (str): Subject/title of the message, ought to be short.
            message (str): Actual message in plain text.
            timeout (int, optional): How much time to wait before giving up. Defaults to 30.

        Returns:
            bool: True if succeeded, False if failed.
        """
        try:
            # if user hasn't changed default sender, do not even try to send email
            default_sender: str = "name.surname@example.mail.com"
            if secret["email_sender"]["username"] == "name.surname@example.mail.com":
                logging.warning(
                    f"will not send email because user hasn't changed default sender '{default_sender}', ignoring"
                )
                return False
            # sender
            sender_email: str = secret["email_sender"]["username"]  # name@example.com
            password: str = secret["email_sender"]["password"]  # 123abc
            port: int = secret["email_sender"]["port"]  # 465
            smtp_server: str = secret["email_sender"]["server"]  # mail.example.com
            # list of receivers
            receiver_emails: list = secret["email_receivers"]  # ["jeff@mail.com"]
        except Exception as e:
            logging.error(f"failed to setup e-mail variables ({e}), please fix this")
            return False
        try:
            # send emails to all receivers
            context = create_default_context()
            with SMTP_SSL(
                smtp_server, port, context=context, timeout=timeout
            ) as server:
                server.login(sender_email, password)
                # for each receiver, create a formatted email and send it
                for target in receiver_emails:
                    try:
                        mail_obj = FormattedEmail(
                            source=sender_email,
                            destination=target,
                            subject=subject,
                            message=message,
                        )
                        server.sendmail(sender_email, target, mail_obj.text)
                    except Exception as e:
                        logging.warning(
                            f"failed to send e-mail message to '{target}' ({e}), ignoring"
                        )
                        continue
                    else:
                        logging.info(f"ok: sent e-mail message to '{target}'")
                        continue
            logging.debug(
                f"ok: completed sending e-mail messages to all targets '{receiver_emails}'"
            )
            return True
        except Exception as e:
            logging.warning(f"failed to send e-mail ({e}), ignoring")
            return False
