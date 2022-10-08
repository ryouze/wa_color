# -*- coding: utf-8 -*-
"""
Get placeholders for files that are empty or corrupted: config, secret, plan, cancel.
"""


def config() -> dict:
    """
    Return user-defined config dictionary (URLs, booleans).

    Returns:
        dict: Placeholder config.
    """
    r: dict = {
        "TARGET": {
            "group_pattern": "^1.*LMT",  # regex: students' group name
        },
        "URL": {
            "cancel": "https://wa.amu.edu.pl/wa/Nieobecnosci_WA/",
            "plan_base": "https://wa.amu.edu.pl/timetables/",
            "plan": "https://wa.amu.edu.pl/timetables/zima_2022_2023/groups/index.html",
        },
        "RUNTIME": {
            "loop_time_in_seconds": 0,  # set to 0 so program will quit after first run
            "send_email_plan": True,
            "send_email_cancel": True,
        },
    }
    return r


def secret() -> dict:
    """
    Return user-defined secret dictionary (e-mails, passwords).

    Returns:
        dict: Placeholder secret.
    """
    r: dict = {
        "email_sender": {
            "username": "name.surname@example.mail.com",
            "password": "123",
            "port": 465,
            "server": "example.mail.com",
        },
        "email_receivers": ["name.surname@mail.com"],
    }
    return r


def plan() -> dict:
    """
    Return program-defined lesson plan dictionary.

    Returns:
        dict: Placeholder lesson plan.
    """
    # empty string causes json serialization error because it's treated as a set
    temp_day: list = ["null" for i in range(7)]
    base_week: dict = {
        "time": ["08:00", "09:45", "11:30", "13:15", "15:00", "16:45", "18:30"],
        "monday": temp_day,
        "tuesday": temp_day,
        "wednesday": temp_day,
        "thursday": temp_day,
        "friday": temp_day,
    }
    # will always be overwritten on first boot
    r: dict = {
        "current": base_week,
        "previous": base_week,
        "metadata": {
            "current_iteration": 0,
            "current_color": "null",
            "current_link": "null",
            "previous_colors": dict(),
            "previous_links": dict(),
            "last_change_color": "1970-01-01 00:00",
            "last_change_table": "1970-01-01 00:00",
            "last_change_link": "1970-01-01 00:00",
        },
    }
    return r


def cancel() -> dict:
    """
    Return program-defined class cancellations dictionary.

    Returns:
        dict: Placeholder class cancellations.
    """
    # empty string causes json serialization error because it's treated as a set
    temp_dates: dict = dict(
        zip(
            ["1970-01-01 00:{:02d}".format(i + 1) for i in range(20)],
            ["null" for i in range(20)],
        )
    )
    # will always be overwritten on first boot
    r: dict = {
        "current": temp_dates,
        "previous": temp_dates,
        "metadata": {
            "current_iteration": 0,
            "last_change": "1970-01-01 00:00",
        },
    }
    return r
