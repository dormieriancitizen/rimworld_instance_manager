import xmltodict

def mod_about(mod):
    try:
        with open(f"source_mods/{mod}/About/About.xml","rb") as aboutxml:
            try:
                return xmltodict.parse(aboutxml, dict_constructor=dict)
            except xmltodict.xml.parsers.expat.ExpatError:
                return {}
    except FileNotFoundError:
        print(f"Unknown mod: "+mod)
        return mod
    
def get_mods_x(mods,x):
    abouts = {}
    for mod in mods:
        abouts[mod] = mod_about(mod)
    
    xs = {}

    for aboutkey in abouts:
        about = abouts[aboutkey]
        xs[aboutkey] = about["ModMetaData"][x] if "ModMetaData" in about else about["ModMetadata"][x] if "ModMetadata" in about else f"Unknown {x}: {about}"

    return xs

def get_mods_names(mods):
    return get_mods_x(mods,"name")

def get_mods_ids(mods):
    return get_mods_x(mods,"packageId")