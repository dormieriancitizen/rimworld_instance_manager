import mod_parser, requests, json, click, os

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
        
        responseFile = open("response.json","w")
        json.dump(response.json(), responseFile)
        responseFile.close()

        print("Mod info gotten")
    
    modInfo = {}
    with open("response.json", "r") as f:
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