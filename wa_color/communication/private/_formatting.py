# -*- coding: utf-8 -*-
"""
Format an e-mail in the RFC 2822 - Internet Message Format format.
"""
import logging
from platform import python_version, system

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class FormattedEmail:

    # footer appended at the end of every message, same for every instance
    footer: str = f"\nsent from {system().lower()} running python {python_version()}\nsource code: https://github.com/ryouze/wa_color/"

    def __init__(
        self,
        source: str,
        destination: str,
        subject: str,
        message: str,
    ) -> None:
        """
        Create an e-mail in the RFC 2822 - Internet Message Format.

        Args:
            source (str): E-mail address of the sender (e.g., program@mail.com).
            destination (str): E-mail address of the receiver (e.g., markus@mail.com).
            subject (str): Subject/title of the message, ought to be short.
            message (str): Actual message in plain text.
        """
        self._source: str = source
        self._destination: str = destination
        self._subject: str = subject
        self._message: str = message
        return None

    @property
    def msg(self) -> bytes:
        """
        Return email with headers as encoded utf-8 bytes in the RFC 2822 format.

        E.g.,
            From: program@mail.com
            To: markus@mail.com
            Subject: this is a test

            This message was sent with Python's smtplib.

        Returns:
            bytes: Encoded message, including the header.
        """
        # append header before message
        txt = f"From: wa_color <{self._source}>\nTo: {self._destination}\nSubject: {self._subject}\n\n{self._message}\n"
        # append footer containing OS information and link to github
        txt += self.footer
        # encode into utf-8 format so non-ascii (polish) characters work in e-mail
        encoded: bytes = txt.encode("utf8")
        return encoded
