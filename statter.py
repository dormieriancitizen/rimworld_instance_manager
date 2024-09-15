import mod_parser, requests, json, click, os, subprocess, xmltodict, time

def du(path):
    # Du in bytes
    return subprocess.check_output(['du','-sb', path]).split()[0].decode('utf-8')

def source_mods_list(steam_only=None):
    source_mods = [f.path.split("/", 1)[1] for f in os.scandir("source_mods") if f.is_dir()]
    if steam_only:
        source_mods = [f for f in source_mods if f.isnumeric()]
    return source_mods

def loadModInfo():
    if click.confirm("Get new mod info?"):
        print("Getting info")

        # Read from the steam API and write to file

        source_mods = source_mods_list(steam_only=True)

        url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        
        # # Construct the publishedfileids parameter
        # publishedfileids = "&".join(f"publishedfileids%5B{i}%5D={mod_id}" for i, mod_id in enumerate(source_mods))
        
        # # Construct the final URL
        # url = f"https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/?itemcount={len(source_mods)}&{publishedfileids}"

        payload = {"itemcount": len(source_mods)}
        for i in range(len(source_mods)):
            payload[f"publishedfileids[{i}]"] = source_mods[i]

        response = requests.post(url, data=payload)
        
        responseFile = open("data/response.json","w")
        json.dump(response.json(), responseFile)
        responseFile.close()

        print("Mod info gotten")
    
    modInfo = {}
    with open("data/response.json", "r") as f:
        modInfo = json.load(f)

    return modInfo

def getModsBy(modInfo,x):
    modStat = { (mod["title"] if "title" in mod else f"missing-title"):int((mod[x] if x  in mod else 0)) for mod in modInfo["response"]["publishedfiledetails"]}
    modStat = {k: v for k, v in sorted(modStat.items(), key=lambda item: item[1])} # Some dict-sorting hackery
    return modStat

def get_common_mod_authors(modInfo):
    modAuthors = {}
    for mod in modInfo["response"]["publishedfiledetails"]:
        try:
            authors = [author.lstrip() for author in mod_parser.mod_about(mod["publishedfileid"])["ModMetaData"]["author"].split(",")]
        except (KeyError, AttributeError) as err:
            authors = ["unknown"]
        
        for author in authors:
            if author in modAuthors:
                modAuthors[author] += 1
            else:
                modAuthors[author] = 1
    modAuthors = {k: v for k, v in sorted(modAuthors.items(), key=lambda item: item[1])}
    print("".join([f"{author} has made {modAuthors[author]} mods \n" for author in modAuthors]))
    return

def get_common_mod_dependencies(modInfo):
    modDeps = {}
    for mod in modInfo["response"]["publishedfiledetails"]:
        try:
            mod_about = mod_parser.mod_about(mod["publishedfileid"])
            if "modDependencies" in mod_about["ModMetaData"]:
                try:
                    dep = mod_about["ModMetaData"]["modDependencies"]["li"]
                    if "packageId" in dep:
                        dependencies = [dep["packageId"]]
                    else:
                        dependencies = [x["packageId"] for x in dep]
                except TypeError:
                    dependencies = []
            else:
                dependencies = []
        except (KeyError, AttributeError):
            dependencies = ["unknown"]
        
        for dependency in dependencies:
            if dependency in modDeps:
                try:
                    modDeps[dependency].append(mod_about["ModMetaData"]["name"])
                except KeyError:
                    modDeps[dependency].append("Unknown Mod")
            else:
                try:
                    modDeps[dependency] = [mod_about["ModMetaData"]["name"]]
                except KeyError:
                    modDeps[dependency] = ["Unknown Mod"]
    modDeps = {k: v for k, v in sorted(modDeps.items(), key=lambda item: len(item[1]),reverse=True)}

    return modDeps

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
            print("Skipped pid "+pid)
            continue
        count += 1
        ordered_ids[modids[pid]] = count

    return ordered_ids

def mod_metadata():
    if click.confirm("Generate new metadata?"):
        return gen_mod_metadata()
    else:
        return load_mod_metadata()

def load_mod_metadata():
    modd = {}
    with open("data/modd.json","r") as f:
        modd = json.load(f)
    return modd

def gen_mod_metadata():
    start_time = time.time()

    mods = source_mods_list()
    steamd = loadModInfo()
    steam_mods = {mod["publishedfileid"]: mod for mod in steamd["response"]["publishedfiledetails"]}
    sort_order = load_sort_order()

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

        d = {}

        d["id"] = mod
        d["source"] = "STEAM" if mod in steam_mods else "LOCAL"
        d["pid"] = abouts[mod]["packageId"]
        d["name"] = abouts[mod]["name"]
        d["author"] = abouts[mod]["author"] if "author" in abouts[mod] else None
        d["url"] = abouts[mod]["url"] if "url" in abouts[mod] else None
        d["sort"] = sort_order[mod] if mod in sort_order else 1000000000000000

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

        modd[mod] = d

    with open("data/modd.json","w") as f:
        json.dump(modd,f)
    
    print(f"Generated mod metadata in {time.time()-start_time}")

    return modd