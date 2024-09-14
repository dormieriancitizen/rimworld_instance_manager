import regex, requests, mod_parser
from rentryupload import RentryUpload
from urllib.parse import urlparse

def import_rentry(rentry_url):
    r = requests.get(rentry_url)

    modlist = regex.search(r"<article>[\s\S]*</article>",r.text).group()
    mods = regex.findall(r"""(?<=<a [^>]*>)[^<]+(?=</a>)|(?<=<p class="admonition-title">[0-9]*\. )[^<]+(?= {)""",modlist)

    return mods

def compile_rentry(mods,mod_metadata):
    steam_mods = {mod["publishedfileid"]: mod for mod in mod_metadata["response"]["publishedfiledetails"]}


    report = (
        "# RimWorld mod list       ![](https://github.com/RimSort/RimSort/blob/main/docs/rentry_preview.png?raw=true)"
        + f"\nCreated with a bad python script I wrote with a lot of code from RimSort"
        + f"\nMod list was created for game version: 1.5"
        + f"\n\n\n\n!!! note Mod list length: `{len(mods)}`\n"
    )

    names = mod_parser.get_mods_names(mods)

    pids = mod_parser.get_mods_ids(mods)
    count = 0

    for mod in mods:
        count += 1
        name = names[mod]
        if mod in steam_mods:
            preview_url = steam_mods[mod]["preview_url"]+"?imw=100&imh=100&impolicy=Letterbox" if "preview_url" in steam_mods[mod] else "https://github.com/RimSort/RimSort/blob/main/docs/rentry_steam_icon.png?raw=true"
            
            url = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(mod)

            report += f"\n{str(count) + '.'} ![]({preview_url}) [{name}]({url} packageid: {pids[mod]})"

        else:
            url = None
            if url is None:
                report += f"\n!!! warning {str(count) + '.'} {name} " + "{" + f"packageid: {pids[mod]}" + "} " # f-strings don't support the squilly brackets
                
            else:
                report += f"\n!!! warning {str(count) + '.'} [{name}]({url}) " + "{" + f"packageid: {pids[mod]}" + "} "
    
    return report

def upload(text):
    rentry_uploader = RentryUpload(text)
    successful = rentry_uploader.upload_success
    host = urlparse(rentry_uploader.url).hostname if successful else None
    if rentry_uploader.url and host and host.endswith("rentry.co"):  # type: ignore
        print("Upload success")
        print(rentry_uploader.url)
    else:
        print("Failed to upload")
