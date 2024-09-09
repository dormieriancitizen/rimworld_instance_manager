import mod_parser

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
            # print(err)
            authors = ["unknown"]
        
        for author in authors:
            if author in modAuthors:
                modAuthors[author] += 1
            else:
                modAuthors[author] = 1
    modAuthors = {k: v for k, v in sorted(modAuthors.items(), key=lambda item: item[1])}
    print("".join([f"{author} has made {modAuthors[author]} mods \n" for author in modAuthors]))
    return