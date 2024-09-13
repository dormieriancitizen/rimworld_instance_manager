import mod_parser, click

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
        except (KeyError, AttributeError) as err:
            print(err)
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
    modDeps = {k: v for k, v in sorted(modDeps.items(), key=lambda item: item[1])}
    print("".join([f"{dependency} has {len(modDeps[dependency])} dependents \n" for dependency in modDeps]))

    if click.confirm("Get dependents of specific mod?"):
        mod = click.prompt("Which mod? (give id)")
        print("\n".join(modDeps[mod]))

    return 