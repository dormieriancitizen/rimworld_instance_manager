import regex, requests, json
import numpy as np
from urllib.parse import urlparse, unquote
from pathlib import Path
from os import getenv

from logger import Logger as log

def import_rentry(rentry_url):
    r = unquote(requests.get(rentry_url).text)

    mods = regex.findall(r'(?<=packageId:\s)(.*?)(?=\}|\")',r,flags=regex.IGNORECASE)

    return mods

def compile_rentry(modd):
    keys = list(modd.keys())
    vals = list(modd.values())

    sorted_value_index = np.argsort([x["sort"] for x in list(modd.values())])

    modd = {keys[i]: vals[i] for i in sorted_value_index}

    report = (
        f"# RimWorld Mod List: {len(modd)} mods       ![](https://github.com/RimSort/RimSort/blob/main/docs/rentry_preview.png?raw=true)"
        "\nCreated with a bad python script with a lot of borrowed code from RimSort"
        f"\nMod list was created for game version: {Path(getenv('GAME_PATH')+'Version.txt').read_text()}"
        "\n\nLocal mods are marked as yellow labels with packageid in brackets."
        "\nMods not from the current version are marked in red"
        f"\n!!! note Mod list length: `{len(modd)}`\n"
        "\n***"
        "\n# | Mod Name | Info"
        "\n:-: | ------ | :------:"

    )

    count = 0

    for mod in modd:
        pfid = ""
        line = ""

        count += 1
        name = modd[mod]["name"]

        url = modd[mod]["download_link"]

        pid = modd[mod]["pid"]

        line += "\n"
        package_id_string = "{packageid: " + pid + "}"

        # if getenv("RIMWORLD_VERSION") not in modd[mod]["supportedVersions"]:
        #     line += "\n!!! danger "
        # elif modd[mod]["source"] in ("LOCAL","GIT"):
        #     line += ""
        # elif modd[mod]["source"] == "LUDEON":
        #     line += "\n!!! info "
        # elif modd[mod]["source"] == "STEAM":
        #     pass

        # Add the index
        line += str(count) + '.|'

        if modd[mod]["source"] == "STEAM":
            pfid = modd[mod]["pfid"]
        if modd[mod]["source"] == "LUDEON":
            pfid = "https://raw.githubusercontent.com/dormieriancitizen/rimworld_instance_manager/refs/heads/main/resources/ludeon-studios.png"
        if modd[mod]["source"] == "GIT":
            pfid = "https://raw.githubusercontent.com/dormieriancitizen/rimworld_instance_manager/refs/heads/main/resources/github-banner.png"
        if modd[mod]["source"] == "LOCAL":
            pfid = "https://raw.githubusercontent.com/dormieriancitizen/rimworld_instance_manager/refs/heads/main/resources/local-banner.png"

        if pfid:
            # Image
            line += f"![{pid}]({pfid})"+"{100px:56px} "
        

        if not url:
            line += f" {name}"  # f-strings don't support the squilly brackets
        else:
            line += f" [{name}]({url})"

        if modd[mod]["source"] == "LOCAL":
            line += " "+package_id_string   

        line += f"| {"XML" if modd[mod]["xml_only"] else "C#"}"
        report += line

    return report

def upload(text):
    rentry_uploader = RentryUpload(text)
    successful = rentry_uploader.upload_success
    host = urlparse(rentry_uploader.url).hostname if successful else None
    if rentry_uploader.url and host and host.endswith("rentry.co"):  # type: ignore
        pass
    else:
        log().error("Failed to upload")

# Taken wholly from RimPy
BASE_URL = "https://rentry.co"
BASE_URL_RAW = f"{BASE_URL}/raw"
API_NEW_ENDPOINT = f"{BASE_URL}/api/new"
_HEADERS = {"Referer": BASE_URL}

class HttpClient:
    def __init__(self) -> None:
        # Initialize a session for making HTTP requests
        self.session = requests.Session()

    def make_request(
        self,
        method: str,
        url: str,
        data: dict[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        # Perform a HTTP request and return the response
        headers = headers or {}
        request_method = getattr(self.session, method.lower())
        response = request_method(url, data=data, headers=headers)
        response.data = response.text
        return response

    def get(self, url: str, headers: dict[str, str] | None = None) -> requests.Response:
        return self.make_request("GET", url, headers=headers)

    def post(
        self,
        url: str,
        data: dict[str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self.make_request("POST", url, data=data, headers=headers)

    def get_csrf_token(self) -> str | None:
        # Get CSRF token from the response cookies after making a GET request to the base URL
        response = self.get(BASE_URL)
        return response.cookies.get("csrftoken")


class RentryUpload:
    def __init__(self, text: str):
        self.upload_success = False
        self.url = None

        try:
            response = self.new(text)
            if response.get("status") != "200":
                self.handle_upload_failure(response)
            else:
                self.upload_success = True
                self.url = response["url"]
        finally:
            if self.upload_success:
                log().log(f"RentryUpload successfully uploaded data! Url: {self.url}\nEdit code: {response['edit_code']}")

    def handle_upload_failure(self, response: dict[str]) -> None:
        """
        Log and handle upload failure details.
        """
        error_content = response.get("content", "Unknown")
        errors = response.get("errors", "").split(".")
        for error in errors:
            log().error(error)

        log().error("RentryUpload failed!")

    def new(self, text: str):
        """
        Upload new entry to Rentry.co.
        """
        # Initialize an HttpClient for making HTTP requests
        client = HttpClient()

        # Get CSRF token for authentication
        csrf_token = client.get_csrf_token()

        # Prepare payload for the POST request
        payload = {
            "csrfmiddlewaretoken": csrf_token,
            "text": text,
        }

        # Perform the POST request to create a new entry
        return json.loads(
            client.post(API_NEW_ENDPOINT, data=payload, headers=_HEADERS).text
        )