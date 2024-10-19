from statter import fetch
import json, click, time, xmltodict, os, asyncio

from logger import Logger as log
from statter.individual_mod import individual_mod

from colorama import Style, Fore, Back

dlcs = ("Core","Biotech","Ideology","Royalty","Anomaly")

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

async def load_mod_metadata():
    with open("data/modd.json","r") as f:
        return json.load(f)  

def mod_metadata(sort_by = None, index_by = None, prune_by = None, fetch=None,include_ludeon=False,always_prompt=False):
    if fetch is None:
        if os.path.exists("data/modd_dirty") or always_prompt:
            fetch = click.confirm("Generate new metadata?")
        else:
            log().info("Data is not marked dirty, sending cached")
            fetch = False
    
    if fetch:
        modd = asyncio.run(gen_mod_metadata(steam_fetch=click.confirm("Fetch new mod info?")))
    else:
        modd = asyncio.run(load_mod_metadata())
  
    if not include_ludeon:
        modd = {e: modd[e] for e in modd if e not in dlcs}
    if prune_by:
        if include_ludeon:
            prune_by.extend(dlcs)
        modd = {e: modd[e] for e in modd if e in prune_by}
    if sort_by:
        modd = dict(sorted(modd.items(), key=lambda item: float(item[1][sort_by])))
    if index_by:
        modd = {modd[e][index_by]:modd[e] for e in modd}
    return modd

async def load_abouts(mods):
    abouts = {}

    time_to_about = time.time()

    tasks = [mod_about(mod) for mod in mods if mod not in dlcs]

    tasks.extend([mod_about(dlc,path=f"/home/dormierian/Games/rimworld/Data/{dlc}/About/About.xml") for dlc in dlcs])

    results = await asyncio.gather(*tasks)

    for mod, about in zip(mods, results):
        if "ModMetaData" in about:
            abouts[mod] = about["ModMetaData"]
        elif "ModMetadata" in about:
            abouts[mod] = about["ModMetadata"]
        else:
            abouts[mod] = None
    
    log().info(f"Loaded about.xmls in {time.time()-time_to_about}")

    return abouts

async def gen_mod_metadata(steam_fetch=False,mods=None):
    if mods is None:
        update = False
        mods = fetch.source_mods_list()
        mods.extend(dlcs)
    else:
        update = True
        modd_task = asyncio.create_task(load_mod_metadata())
    
    # Don't include time to fetch mod info
    steam_mods = [mod for mod in mods if fetch.is_steam_mod(mod)]
    local_mods = [mod for mod in mods if mod not in steam_mods]
    start_time = time.time()

    abouts_task = asyncio.create_task(load_abouts(mods))
    steam_task = asyncio.create_task(fetch.fetch_steam_info(fetch=steam_fetch,mods=steam_mods))

    abouts = await abouts_task
    time_to_generate = time.time()

    # We can start the local mods once abouts are generated
    tasks = [asyncio.create_task(individual_mod(mod,None,abouts[mod])) for mod in local_mods]

    steam_modds = await steam_task
    tasks.extend([asyncio.create_task(individual_mod(mod,(steam_modds[mod] if mod in steam_modds else None),abouts[mod])) for mod in steam_mods])
    
    results = await asyncio.gather(*tasks)
    partial_modd = {result["id"]: result for result in results}
    
    if update:
        modd = await modd_task
        modd.update(partial_modd)
    else:
        modd = partial_modd

    log().info(f"Processed info in {time.time()-time_to_generate}")

    with open("data/modd.json","w") as f:
        json.dump(modd,f)
    
    log().info(f"Generated{" partial" if update else ""} metadata for {len(mods)} mods in {time.time()-start_time}")
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
