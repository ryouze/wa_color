"""
Create HTML file based on lessson plan.
"""
import logging

# setup per-module logger
log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class HtmlManager:
    """ """

    def __init__(self, file_instance) -> None:
        """
        Create HTML comparison file from two table - current lesson plan and previous lesson plan.

        _extended_summary_

        Args:
            file_instance (obj): An instance of the File Manager class that accesses JSON files from disk.
        """
        self.file_instance = file_instance
        # get current lesson plan from plan.json
        try:
            # reorder manually, instead of alphabetically
            table_current: dict = file_instance.plan["current"]
            self.week_current = {
                "Time": table_current["time"],
                "Monday": table_current["monday"],
                "Tuesday": table_current["tuesday"],
                "Wednesday": table_current["wednesday"],
                "Thursday": table_current["thursday"],
                "Friday": table_current["friday"],
            }
            self.date_current: str = file_instance.plan["metadata"]["last_change_table"]
            table_previous: dict = file_instance.plan["previous"]
            self.week_previous = {
                "Time": table_previous["time"],
                "Monday": table_previous["monday"],
                "Tuesday": table_previous["tuesday"],
                "Wednesday": table_previous["wednesday"],
                "Thursday": table_previous["thursday"],
                "Friday": table_previous["friday"],
            }
        except Exception as e:
            logging.error(
                f"failed to extract the lesson plan table using the file instance ({e})"
            )
            raise
        # cached variable
        self._html: str = str()
        return None

    @staticmethod
    def _get_html_start() -> str:
        """
        Get beginning of the HTML.

        Contains: html, head, style and body opener.

        Returns:
            str: HTML file (beginning).
        """
        return """<!DOCTYPE html>
<html lang="en">
<html>

<head>
    <meta charset="utf-8" />
    <title> lesson plan </title>
    <meta content="automatically generated lesson plan" name="description" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <style type="text/css">
        body {
            background-color: black;
            color: white;
            font-family: Arial, Helvetica, sans-serif;
            height: 100%;
            margin-bottom: 100px;
            overflow-wrap: break-word;
            overflow-y: scroll;
        }

        /* do not stretch when padding or border is added */
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        h1 {
            color: #d3d3d3;
            font-size: 120%;
            padding-bottom: 10px;
            padding-top: 30px;
            text-align: center;
        }

        table {
            background-color: #141414;
            margin-bottom: 20px;
            margin-left: auto;
            margin-right: auto;
            table-layout: auto;
            text-align: center;
            width: 1000px;
        }

        table,
        th,
        td {
            border-collapse: collapse;
            border: 1px solid #262626;
        }

        /* columns */
        table th {
            color: #b3b3b3;
            font-size: 95%;
            font-weight: bold;
            letter-spacing: 0.1em;
            padding: 12px;
        }

        /* rows */
        table td {
            color: #808080;
            font-size: 85%;
            letter-spacing: 0.02em;
            padding: 10px;
        }

        tr:nth-child(even) {
            background-color: #1a1a1a;
        }

        /* narrow */
        @media only screen and (max-width: 1048px) {
            table {
                width: 95%;
            }
        }

        /* mobile */
        @media only screen and (max-width: 680px) {
            table {
                width: 100%;
            }

            table th {
                font-size: 75%;
            }

            table td {
                font-size: 65%;
            }
        }

    </style>
</head>

<body>"""

    @staticmethod
    def _week_to_table(week: dict) -> str:
        """
        Convert week dictionary to a HTML table.

        This is used every time we need to turn JSON into HTML.

        Args:
            week (dict): lesson plan JSON.

        Returns:
            str: HTML file (table).
        """
        r: str = f"\n{' ' * 4}<table>\n"
        r += (
            f"{' ' * 8}<tr>\n{' ' * 12}<th>"
            + f"</th>\n{' ' * 12}<th>".join(week.keys())
            + f"</th>\n{' ' * 12}</tr>\n"
        )
        # append all classes
        for row in zip(*week.values()):
            # replace newlines with <br> (html newline)
            row: list = [i.replace("\n", "<br>") for i in row]
            r += (
                f"{' ' * 8}<tr>\n{' ' * 12}<td>"
                + f"</td>\n{' ' * 12}<td>".join(row)
                + f"</td>\n{' ' * 8}</tr>\n"
            )
        r += f"{' ' * 4}</table>"
        return r

    def _create_html(self) -> str:
        """
        Create full HTML document.

         Contains: head, style, body (with two tables).

        Returns:
            str: HTML file (full).
        """
        # get beginning of the document (head, style and body opener)
        html: str = self._get_html_start()
        html += f"\n{' ' * 4}<h1>--- current plan @ {self.date_current} ---</h1>"
        html += self._week_to_table(self.week_current)
        html += f"\n{' ' * 4}<h1>--- previous plan ---</h1>"
        html += self._week_to_table(self.week_previous)
        # close table, body and html
        html += "\n</body>\n\n</html>\n"
        return html

    @property
    def html(self) -> str:
        """
        Get HTML file - if cache unavailable, process now.

        Returns:
            dict: Contents of the file.
        """
        logging.debug("GET: HTML (try to load from cache, then create now)")
        if not self._html:
            logging.debug("html not cached, creating now")
            self._html = self._create_html()
        else:
            logging.debug("ok: html was cached, returning from RAM")
        return self._html

    def save(self) -> bool:
        """
        Save HTML file to disk.

        This combines two lesson plans - current and previous.

        Returns:
            bool: True if succeeded, False if failed.
        """
        try:
            self.file_instance.html = self.html
        except Exception as e:
            logging.error(f"failed to write html file ({e})")
            return False
        else:
            logging.info("ok: saved html file")
        return True
