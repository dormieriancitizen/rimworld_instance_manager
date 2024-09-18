import mod_parser, requests, json, click, os, xmltodict, time

from helpers import du
from colorama import Fore, Back, Style

def source_mods_list(steam_only=None):
    source_mods = [f.path.split("/", 1)[1] for f in os.scandir("source_mods") if f.is_dir()]
    if steam_only:
        source_mods = [f for f in source_mods if f.isnumeric()]
    return source_mods

def fetch_mod_info(fetch=False,mods=None):
    if fetch or click.confirm("Fetch new mod info?"):
        start_time = time.time()

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

        response = requests.post(url, data=payload)
        
        responseFile = open("data/response.json","w")
        json.dump(response.json(), responseFile)
        responseFile.close()

        print(f"{Style.DIM}Fetched from steam in {time.time()-start_time}{Style.RESET_ALL}")
    
    modInfo = {}
    with open("data/response.json", "r") as f:
        modInfo = json.load(f)

    return modInfo

def load_sort_order(mods):
    sorder = {}
    with open("/home/dormierian/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml","rb") as ModsConfig:
        sorder = xmltodict.parse(ModsConfig, dict_constructor=dict)
    
    sorder = sorder["ModsConfigData"]["activeMods"]["li"]

    modids = mod_parser.get_mods_x(mods,"packageId")
    modids = {v.lower(): k for k, v in modids.items()}

    ordered_ids = {}

    count = 0
    for pid in sorder:
        if pid.startswith("ludeon."):
            print(Style.DIM + "Skipped pid "+pid + Style.RESET_ALL)
            continue
        count += 1
        ordered_ids[modids[pid]] = count

    return ordered_ids

def load_mod_metadata():
    with open("data/modd.json","r") as f:
        return json.load(f)  

def mod_metadata(sort_by = None, index_by = None, prune_by = None, fetch=False, steam_fetch = None):
    if fetch or click.confirm("Generate new metadata?"):
        if steam_fetch:
            modd = gen_mod_metadata(steam_fetch=steam_fetch)
        else:    
            modd = gen_mod_metadata()
    else:
        modd = load_mod_metadata()
  
    if prune_by:
        modd = {e: modd[e] for e in modd if e in prune_by}
    if sort_by:
        modd = dict(sorted(modd.items(), key=lambda item: int(item[1][sort_by])))
    if index_by:
        modd = {modd[e][index_by]:modd[e] for e in modd}
    return modd

def individual_mod(mod,steam_mods,sort_order,abouts):
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
    else:
        d["source"] = "LOCAL"
    
    d["name"] = abouts[mod]["name"] if "name" in abouts[mod] else d["pid"]
    d["author"] = abouts[mod]["author"] if "author" in abouts[mod] else None
    d["url"] = abouts[mod]["url"] if "url" in abouts[mod] else None
    d["sort"] = sort_order[mod] if mod in sort_order else 1000000000000000

    deps = []
    if "modDependencies" in abouts[mod]:
        if abouts[mod]["modDependencies"]:
            if abouts[mod]["modDependencies"]["li"]:
                deps = abouts[mod]["modDependencies"]["li"]
                deps = [deps] if isinstance(deps,dict) or isinstance(deps,str) else deps
                deps = [dep["packageId"].lower() for dep in deps]
            else:
                deps = []
    else:
        deps = []
    d["deps"] = deps

    deps = []
    if "loadBefore" in abouts[mod]:
        if abouts[mod]["loadBefore"]:
            if abouts[mod]["loadBefore"]["li"]:
                deps = abouts[mod]["loadBefore"]["li"]
                deps = [deps] if isinstance(deps,dict) or isinstance(deps,str) else deps
                deps = [dep.lower() for dep in deps]
            else:
                deps = []
    else:
        deps = []
    d["loadBefore"] = deps

    deps = []
    if "loadAfter" in abouts[mod]:
        if abouts[mod]["loadAfter"]:
            if abouts[mod]["loadAfter"]["li"]:
                deps = abouts[mod]["loadAfter"]["li"]
                deps = [deps] if isinstance(deps,dict) or isinstance(deps,str) else deps
                deps = [dep.lower() for dep in deps]
            else:
                deps = []
    else:
        deps = []
    d["loadAfter"] = deps

    if d["source"] == "STEAM":
        d["download_link"] = "https://steamcommunity.com/workshop/filedetails/?id="+mod
        d["size"] = steam_mods[mod]["file_size"] if "file_size" in steam_mods[mod] else du("source_mods/"+mod)
        d["subs"] = str(steam_mods[mod]["lifetime_subscriptions"]) if "lifetime_subscriptions" in steam_mods[mod] else "0"
        d["pfid"] = f"{steam_mods[mod]["preview_url"]}?imw=100&imh=100&impolicy=Letterbox" if "preview_url" in steam_mods[mod] else "https://github.com/RimSort/RimSort/blob/main/docs/rentry_steam_icon.png?raw=true"

        d["time_created"] = str(steam_mods[mod]["time_created"]) if "time_created" in steam_mods[mod] else "0"
        d["time_updated"] = str(steam_mods[mod]["time_updated"]) if "time_updated" in steam_mods[mod] else "0"
        with open(f"source_mods/{mod}/timeDownloaded","r") as f:
            d["time_downloaded"] = f.readlines()[0]

    else:
        d["download_link"] = d["url"] if d["url"] else ""
        d["size"] = du("source_mods/"+mod)
        d["subs"] = "0"
        d["pfid"] = "0"

        d["time_created"] = "0"
        d["time_updated"] = "0"
        d["time_downloaded"] = "0"
    
    return d

def gen_mod_metadata(fetch=None):
    if fetch:
        steamd = fetch_mod_info()
    else:
        steamd = fetch_mod_info(fetch=True)

    # Don't include time to fetch mod info
    start_time = time.time()

    mods = source_mods_list()
    steam_mods = {mod["publishedfileid"]: mod for mod in steamd["response"]["publishedfiledetails"]}
    
    sort_order = load_sort_order(mods)

    abouts = {}

    for mod in mods:
        about = mod_parser.mod_about(mod)
        if "ModMetaData" in about:
            abouts[mod] = about["ModMetaData"]
        elif "ModMetadata" in about:
            abouts[mod] = about["ModMetadata"]
        else:
            abouts[mod] = None
    
    modd = {}
    count = 0
    for mod in mods:
        count += 1
        modd[mod] = individual_mod(mod,steam_mods,sort_order,abouts)

    with open("data/modd.json","w") as f:
        json.dump(modd,f)
    
    print(f"{Style.DIM}Generated metadata for {count} mods in {time.time()-start_time}{Style.RESET_ALL}")
    return modd

def partial_metadata_regen(mods):
    start_time = time.time()

    modd = load_mod_metadata()

    steamd = fetch_mod_info(fetch=True,mods=mods)
    steam_mods = {mod["publishedfileid"]: mod for mod in steamd["response"]["publishedfiledetails"]}
    sort_order = load_sort_order(mods)

    abouts = {}
    for mod in mods:
        about = mod_parser.mod_about(mod)
        if "ModMetaData" in about:
            abouts[mod] = about["ModMetaData"]
        elif "ModMetadata" in about:
            abouts[mod] = about["ModMetadata"]
        else:
            abouts[mod] = None

    for mod in mods:
        count += 1
        modd[mod] = individual_mod(mod,steam_mods,sort_order,abouts)

    with open("data/modd.json","w") as f:
        json.dump(modd,f)  
    
    print(f"{Style.DIM}Generated partial metadata for {count} mods in {time.time()-start_time}{Style.RESET_ALL}")
    return modd


def instance_metadata(modlist):
    modd = mod_metadata(prune_by=modlist,index_by="pid",fetch=False)
    comun_rules = fetch_rimsort_community_rules()["rules"]
    comun_rules = {x: comun_rules[x] for x in comun_rules if x in modd}

    for mod in comun_rules:
        if "loadBefore" in comun_rules[mod]:
            for rule in comun_rules[mod]["loadBefore"]:
                if rule in modd and not rule in modd[mod]["loadBefore"]:
                    modd[mod]["loadBefore"].append(rule.lower())
        if "loadAfter" in comun_rules[mod]:
            for rule in comun_rules[mod]["loadAfter"]:
                if rule in modd and not rule in modd[mod]["loadAfter"]:
                    modd[mod]["loadAfter"].append(rule.lower())
    return modd

def fetch_rimsort_community_rules():
    os.system("git -C data/rs_rules pull")
    with open("data/rs_rules/communityRules.json", "r") as f:
        return json.load(f)