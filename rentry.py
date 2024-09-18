import regex, requests
import numpy as np
from rentryupload import RentryUpload
from urllib.parse import urlparse

def import_rentry(rentry_url):
    r = requests.get(rentry_url)

    modlist = regex.search(r"<article>[\s\S]*</article>",r.text).group()
    mods = regex.findall(r"""(?<=<a [^>]*>)[^<]+(?=</a>)|(?<=<p class="admonition-title">[0-9]*\. )[^<]+(?= {)""",modlist)

    return mods

def compile_rentry(modd):
    keys = list(modd.keys())
    vals = list(modd.values())

    sorted_value_index = np.argsort([x["sort"] for x in list(modd.values())])

    modd = {keys[i]: vals[i] for i in sorted_value_index}

    report = (
        "# RimWorld mod list       ![](https://github.com/RimSort/RimSort/blob/main/docs/rentry_preview.png?raw=true)"
        + f"\nCreated with a bad python script I wrote with a lot of code from RimSort"
        + f"\nMod list was created for game version: 1.5"
        + "\n!!! info Local mods are marked as yellow labels with packageid in brackets."
        + f"\n\n\n\n!!! note Mod list length: `{len(modd)}`\n"
    )

    count = 0

    for mod in modd:
        count += 1
        name = modd[mod]["name"]
        url = modd[mod]["download_link"]
        pid = modd[mod]["pid"]

        if modd[mod]["source"] == "STEAM":
            preview_url = modd[mod]["pfid"]
            report += f"\n{str(count) + '.'} ![]({preview_url}) [{name}]({url} packageid: {pid})"

        else:
            if url is None:
                report += f"\n!!! warning {str(count) + '.'} {name} " + "{" + f"packageid: {pid}" + "} " # f-strings don't support the squilly brackets
                
            else:
                report += f"\n!!! warning {str(count) + '.'} [{name}]({url}) " + "{" + f"packageid: {pid}" + "} "
    
    return report

def upload(text):
    rentry_uploader = RentryUpload(text)
    successful = rentry_uploader.upload_success
    host = urlparse(rentry_uploader.url).hostname if successful else None
    if rentry_uploader.url and host and host.endswith("rentry.co"):  # type: ignore
        pass
    else:
        print("Failed to upload")
