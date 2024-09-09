import os, xmltodict

def mod_about(mod):
    try:
        with open(f"source_mods/{mod}/About/About.xml","rb") as aboutxml:
            return xmltodict.parse(aboutxml, dict_constructor=dict)
    except FileNotFoundError:
        return None

def get_mods_names(mods):
    abouts = []
    for mod in mods:
        abouts.append(mod_about(mod))
    
    names = [about["ModMetaData"]["name"] for about in abouts]
    return names