import xmltodict, os

def mod_about(mod, path=None):
    if path == None:
        if os.path.exists(f"source_mods/{mod}/About/About.xml"):
            path = f"source_mods/{mod}/About/About.xml"
        elif os.path.exists(f"source_mods/{mod}/About/about.xml"):
            path = f"source_mods/{mod}/About/about.xml"
    else:
        if not os.path.exists(path):
            raise Exception(f"Passed nonexistent path {path}")
    
    try:
        with open(path,"rb") as aboutxml:
            try:
                return xmltodict.parse(aboutxml, dict_constructor=dict)
            except xmltodict.xml.parsers.expat.ExpatError:
                return {}
    except TypeError:
        print(path,mod)
        raise Exception("bugg")
    except FileNotFoundError:
        print(f"Unknown mod: "+mod)
        raise Exception(f"Passed nonexistent path {path}")
    
def get_mods_x(mods,x):
    abouts = {}
    for mod in mods:
        abouts[mod] = mod_about(mod)
    
    xs = {}

    for aboutkey in abouts:
        about = abouts[aboutkey]
        xs[aboutkey] = about["ModMetaData"][x] if "ModMetaData" in about else about["ModMetadata"][x] if "ModMetadata" in about else f"Unknown {x}: {about}"

    return xs