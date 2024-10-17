import regex, requests
import numpy as np
from rentryupload import RentryUpload
from urllib.parse import urlparse, unquote
from pathlib import Path
from os import getenv

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
        "\n!!! info Local mods are marked as yellow labels with packageid in brackets."
        "\n!!! info Mods not from the current version are marked in red"
        f"\n!!! note Mod list length: `{len(modd)}`\n"
        "\n***"

    )

    count = 0

    for mod in modd:
        count += 1
        name = modd[mod]["name"]

        url = modd[mod]["download_link"]

        pid = modd[mod]["pid"]

        report += "\n"
        package_id_string = "{packageid: " + pid + "}"

        if getenv("RIMWORLD_VERSION") not in modd[mod]["supportedVersions"]:
            report += "\n!!! danger "
        elif modd[mod]["source"] in ("LOCAL","GIT"):
            report += "\n!!! warning "
        elif modd[mod]["source"] == "LUDEON":
            report += "\n!!! info "
        elif modd[mod]["source"] == "STEAM":
            pass

        # Add the index
        report += str(count) + '. '

        if modd[mod]["source"] == "STEAM":
            # Image
            report += f"![{pid}]({modd[mod]["pfid"]})"+" "

        if not url:
            report += f"{name}"  # f-strings don't support the squilly brackets
        else:
            report += f"[{name}]({url})"

        if modd[mod]["source"] != "STEAM":
            report += " "+package_id_string       

    return report

def upload(text):
    rentry_uploader = RentryUpload(text)
    successful = rentry_uploader.upload_success
    host = urlparse(rentry_uploader.url).hostname if successful else None
    if rentry_uploader.url and host and host.endswith("rentry.co"):  # type: ignore
        pass
    else:
        print("Failed to upload")
