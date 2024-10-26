from logger import Logger as log
from statter import sheet_manager

import click, requests, json, time, subprocess, os, asyncio, functools, csv, xmltodict

async def steam_info(fetch=None,mods=None):
    if fetch is None:
        fetch = click.confirm("Fetch new mod info?")

    loop = asyncio.get_event_loop()
    
    start_time = time.time()
    if fetch:
        # Read from the steam API and write to file
        if not mods:
            mods = source_mods_list(steam_only=True)

        url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        
        # # Construct the publishedfileids parameter
        # publishedfileids = "&".join(f"publishedfileids%5B{i}%5D={mod_id}" for i, mod_id in enumerate(source_mods))
        
        # # Construct the final URL
        # url = f"https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/?itemcount={len(source_mods)}&{publishedfileids}"

        payload = {"itemcount": len(mods)}
        for i in range(len(mods)):
            payload[f"publishedfileids[{i}]"] = mods[i]

        steamd = (await loop.run_in_executor(None,functools.partial(requests.post, url, data=payload))).json()
        
        if not mods:
            responseFile = open("data/response.json","w")
            json.dump(steamd, responseFile)
            responseFile.close()
    else:
        with open("data/response.json", "r") as f:
            steamd = json.load(f)
    log().info(f"{"Fetched from steam in " if fetch else "Loaded from steam response file in "}{time.time()-start_time}")

    # Reorganise the response by each ID
    steamd = {mod["publishedfileid"]: mod for mod in steamd["response"]["publishedfiledetails"]}

    return steamd

def fetch_rimsort_community_rules():
    subprocess.Popen("git -C data/rs_rules pull",shell=True,stdout=subprocess.DEVNULL).wait()
    with open("data/rs_rules/communityRules.json", "r") as f:
        return json.load(f)

def is_steam_mod(mod):
    if not mod.isnumeric():
        return False
    if not len(mod) >= 9:
        return False
    if not len(mod) <= 10:
        return False
    else:
        return True

def source_mods_list(steam_only=None):
    source_mods = [f.path.split("/", 1)[1] for f in os.scandir("source_mods") if f.is_dir()]
    if steam_only:
        source_mods = [f for f in source_mods if is_steam_mod(f)]
    return source_mods

def get_modlist(instance,fetch=None):
    mods = []

    if fetch is None:
        fetch = click.confirm("Get modlist from sheet?")

    if fetch:
        mods = sheet_manager.get_modlist_info(instance)
        with open(f"instances/{instance}/modlist.csv","w") as instance_csv:
            instance_csv.write(mods)
        reader = csv.reader(mods.splitlines(),delimiter=",")
        for row in reader:
            mods=row
            break
    else:
        with open(f"instances/{instance}/modlist.csv","r") as instance_csv:
            reader = csv.reader(instance_csv)
            for row in reader:
                mods=row
                break
    
    return mods


async def mod_about(mod, path=None):
    if path == None:
        if os.path.exists(f"source_mods/{mod}/About/About.xml"):
            path = f"source_mods/{mod}/About/About.xml"
        elif os.path.exists(f"source_mods/{mod}/About/about.xml"):
            path = f"source_mods/{mod}/About/about.xml"
        else:
            log().error(f"Could not find path for {mod}, was passed {path}")
    else:
        if not os.path.exists(path):
            raise Exception(f"Passed nonexistent path {path}")
    
    try:
        with open(path,"rb") as aboutxml:
            try:
                return xmltodict.parse(aboutxml, dict_constructor=dict)
            except xmltodict.xml.parsers.expat.ExpatError:
                log().error(f"Expat error in "+path)
                return {}
    
    except FileNotFoundError:
        log().error(f"Unknown mod: "+mod)
        raise Exception(f"Passed nonexistent path {path}")

def get_mods_from_modsconfig(path):
    with open(path,"rb") as modsconfigs_file:
        modsconfigs = xmltodict.parse(modsconfigs_file,dict_constructor=dict)

    return modsconfigs["ModsConfigData"]["activeMods"]["li"]
    