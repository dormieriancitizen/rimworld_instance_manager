from statter import mod_parser, fetch
import json, click, time

from statter.individual_mod import individual_mod

from colorama import Style, Fore, Back

def load_mod_metadata():
    with open("data/modd.json","r") as f:
        return json.load(f)  

def mod_metadata(sort_by = None, index_by = None, prune_by = None, fetch=None,include_ludeon=False):
    if fetch is None:
        fetch = click.confirm("Generate new metadata?")
    if fetch:
            modd = gen_mod_metadata()
    else:
        modd = load_mod_metadata()
  
    if prune_by:
        modd = {e: modd[e] for e in modd if e in prune_by}
    if include_ludeon:
        dlcs = ["Core","Biotech","Ideology","Royalty","Anomaly"]
        abouts = {dlc: mod_parser.mod_about(dlc,path=f"/home/dormierian/Games/rimworld/Data/{dlc}/About/About.xml")["ModMetaData"] for dlc in dlcs}

        for dlc in dlcs:
            modd[dlc] = individual_mod(dlc,{},abouts)
    if sort_by:
        modd = dict(sorted(modd.items(), key=lambda item: float(item[1][sort_by])))
    if index_by:
        modd = {modd[e][index_by]:modd[e] for e in modd}
    return modd

def gen_mod_metadata():
    steam_mods = fetch.fetch_steam_info()

    # Don't include time to fetch mod info
    start_time = time.time()
    mods = fetch.source_mods_list()

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
        modd[mod] = individual_mod(mod,steam_mods,abouts)

    with open("data/modd.json","w") as f:
        json.dump(modd,f)
    
    print(f"{Style.DIM}Generated metadata for {count} mods in {time.time()-start_time}{Style.RESET_ALL}")
    return modd

def partial_metadata_regen(mods,refetch=True):
    start_time = time.time()
    modd = load_mod_metadata()
    steam_mods = fetch.fetch_steam_info(fetch=refetch,mods=mods)

    abouts = {}
    for mod in mods:
        about = mod_parser.mod_about(mod)
        if "ModMetaData" in about:
            abouts[mod] = about["ModMetaData"]
        elif "ModMetadata" in about:
            abouts[mod] = about["ModMetadata"]
        else:
            abouts[mod] = None

    count = 0 
    for mod in mods:
        count += 1
        modd[mod] = individual_mod(mod,steam_mods,abouts)

    with open("data/modd.json","w") as f:
        json.dump(modd,f)  
    
    print(f"{Style.DIM}Generated partial metadata for {count} mods in {time.time()-start_time}{Style.RESET_ALL}")
    return modd

def instance_metadata(modlist):
    modd = mod_metadata(prune_by=modlist,index_by="pid",fetch=False,include_ludeon=True)

    comun_rules = fetch.fetch_rimsort_community_rules()["rules"]
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
