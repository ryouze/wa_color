# -*- coding: utf-8 -*-
"""
API for sending e-mail messages.
"""
from smtplib import SMTP_SSL
from ssl import create_default_context
import logging

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
            sender_email: str = secret["email_sender"]["username"]  # Enter your address
            password: str = secret["email_sender"]["password"]
            port: int = secret["email_sender"]["port"]
            smtp_server: str = secret["email_sender"]["server"]
            # list of receivers
            receiver_emails: list = secret["email_receivers"]
        except Exception as e:
            logging.warning(f"failed to setup e-mail variables ({e}), ignoring")
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
                        to_send = FormattedEmail(
                            source=sender_email,
                            destination=target,
                            subject=subject,
                            message=message,
                        )
                        server.sendmail(sender_email, target, to_send.text)
                    except Exception as e:
                        logging.warning(
                            f"failed to send e-mail message to '{target}' ({e})"
                        )
                        continue
                    else:
                        logging.debug(f"ok: sent e-mail message '{target}'")
                        continue
            logging.debug(f"completed sending e-mail messages to '{receiver_emails}'")
            return True
        except Exception as e:
            logging.warning(f"failed to send e-mail ({e}), ignoring")
            return False
