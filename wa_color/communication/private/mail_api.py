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


def send(
    secret: dict,
    subject: str,
    message: str,
    timeout: int = 30,
) -> bool:
    """
    Send plain-text e-mail messages to all receivers.

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
    has_succeeded: bool = False
    try:
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
                timeout=timeout,
            ) as server:
                server.login(sender_email, password)
                logging.debug(
                    f"ok: logged into '{sender_email}', now trying to send e-mails to '{receiver_emails}'"
                )
                # for each receiver, create a formatted email and send it
                for target in receiver_emails:
                    mail_obj = FormattedEmail(
                        source=sender_email,
                        destination=target,
                        subject=subject,
                        message=message,
                    )
                    # contains header, everything is encoded in utf-8
                    msg: bytes = mail_obj.msg
                    logging.debug(f"trying to send e-mail to '{target}'")
                    server.sendmail(sender_email, target, msg)
                    logging.info(f"ok: sent e-mail message to '{target}'")
                    continue
        except Exception as e:
            logging.warning(
                f"failed to send e-mails to '{receiver_emails}' ({e}), ignoring"
            )
        else:
            logging.debug(f"ok: sent e-mails to '{receiver_emails}'")
            has_succeeded = True
    finally:
        return has_succeeded
