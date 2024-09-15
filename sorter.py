# The Legendary Sorting Machine
# it doesnt work

import xmltodict, mod_parser

class Mod:
    def __init__(self,deps,modid):
        self.deps = deps
        self.id = modid

def load_sort_order(mods):
    sorder = {}
    with open("/home/dormierian/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml","rb") as ModsConfig:
        sorder = xmltodict.parse(ModsConfig, dict_constructor=dict)
    
    sorder = sorder["ModsConfigData"]["activeMods"]["li"]

    modids = mod_parser.get_mods_ids(mods)
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