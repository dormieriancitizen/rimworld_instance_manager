import subprocess, time, os
from pathlib import Path

from colorama import Style, Fore, Back

# SETTINGS
VERSION = "1.5"

def individual_mod(mod,steam_mods,abouts):
    def read_li(atr):
        nonlocal abouts

        items = []
        if atr in abouts[mod]:
            if abouts[mod][atr]:
                if abouts[mod][atr]["li"]:
                    items = abouts[mod][atr]["li"]

                    # If there's more than one li, then its already list, otherwise, make it a list.
                    items = [items] if isinstance(items,dict) or isinstance(items,str) else items
                else:
                    items = []
        else:
            items = []
        return items

    def du(path):
        # Du in bytes
        return subprocess.check_output(['du','-sb', path.as_posix()]).split()[0].decode('utf-8')

    mod_path = Path("source_mods") / mod

    d = {}
    d["id"] = mod

    if "packageId" in abouts[mod]:
        d["pid"] = abouts[mod]["packageId"].lower()  
    else:
        raise Exception(f"Mod {mod} has no pid")

    if d["pid"].startswith("ludeon."):
        d["source"] = "LUDEON"
    elif mod in steam_mods:
        d["source"] = "STEAM"
    elif (mod_path / ".git").is_dir():
        d["source"] = "GIT"
    else:
        d["source"] = "LOCAL"
    

    d["name"] = abouts[mod]["name"] if "name" in abouts[mod] else d["pid"]
    d["author"] = abouts[mod]["author"] if "author" in abouts[mod] else ""
    d["url"] = abouts[mod]["url"] if "url" in abouts[mod] else ""

    d["deps"] = [dep["packageId"].lower() for dep in read_li("modDependencies")]
    d["loadBefore"] = [dep.lower() for dep in read_li("loadBefore")]
    d["loadAfter"] = [dep.lower() for dep in read_li("loadAfter")]

    d["supportedVersions"] = read_li("supportedVersions")

    if d['source'] != 'LUDEON':
        time_first_downloaded_file =  mod_path / "time_initially_downloaded"
        if time_first_downloaded_file.exists():
            d["time_first_downloaded"] = time_first_downloaded_file.read_text()
        else:
            print(f"{d['source']} mod {d["name"]} has no inital download time. Setting to now.")
            now = str(time.time() * 1000)
            time_first_downloaded_file.write_text(now)
            d["time_first_downloaded"] = now

        time_downloaded_file = mod_path / "timeDownloaded"
        if time_downloaded_file.exists():
            d["time_downloaded"] = time_downloaded_file.read_text()
        else:
            print(f"{d['source']} mod {d["name"]} has no current download time. Setting to 0{" (will be downloaded again on next update)." if d["source"] == "STEAM" else "."}")
            time_downloaded_file.write_text("0")
            d["time_downloaded"] = "0"
    else:
        d["time_downloaded"] = "0"
        d['time_first_downloaded'] = "0"
    

    # Check if mod is XML-only
    if d["source"] != "LUDEON":
        # If no assemblies folder, no mod
        assemblies_path = mod_path / VERSION / "Assemblies"

        if not assemblies_path.exists():
            if (mod_path / f"v{VERSION}" / "Assemblies").is_dir():
                assemblies_path = mod_path / f"v{VERSION}" / "Assemblies"
            

        if os.path.isdir(assemblies_path):
            if any(file.endswith(("dll","DLL")) for file in os.listdir(assemblies_path)):
                d["xml_only"] = False
            else:
                d["xml_only"] = True
        else:
            d["xml_only"] = True
    else:
        d["xml_only"] = False

    # Things that depend on steam data

    if d["source"] == "STEAM":
        d["download_link"] = "https://steamcommunity.com/workshop/filedetails/?id="+mod
        d["subs"] = str(steam_mods[mod]["lifetime_subscriptions"]) if "lifetime_subscriptions" in steam_mods[mod] else "0"
        d["pfid"] = f"{steam_mods[mod]["preview_url"]}?imw=100&imh=100&impolicy=Letterbox" if "preview_url" in steam_mods[mod] else "https://github.com/RimSort/RimSort/blob/main/docs/rentry_steam_icon.png?raw=true"

        d["time_created"] = str(steam_mods[mod]["time_created"]*1000) if "time_created" in steam_mods[mod] else "0"
        d["time_updated"] = str(steam_mods[mod]["time_updated"]*1000) if "time_updated" in steam_mods[mod] else "0"

        d["size"] = steam_mods[mod]["file_size"] if "file_size" in steam_mods[mod] else du(mod_path)
    else:
        d["download_link"] = d["url"]
        d["subs"] = "0"
        d["pfid"] = "0"

        d["time_created"] = "0"
        d["time_updated"] = "0"

        if d['source'] == "LUDEON":
            d["size"] = "0"
            d["name"] = mod
        else:
            # This is kind of slow, may change later.
            d["size"] = du(mod_path)
 

    gname = ""
    if VERSION not in d["supportedVersions"]:
        gname += Fore.RED
    else:
        gname += Fore.BLUE
    gname += Style.BRIGHT
    if not d["xml_only"]:
        gname+="©"
    gname += f"[{d["source"]}] "

    gname += d["name"]
    gname += Style.RESET_ALL

    d["graphical_name"] = gname

    return d