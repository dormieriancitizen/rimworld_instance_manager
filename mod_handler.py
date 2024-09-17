import click, os, csv, time
from helpers import *

import statter, sorter

def generate_modlist(instance):
    # Validate modlist
    source_mods  = statter.source_mods_list()
    mods = get_id_list(instance)
    mods, dupes = duplicate_check(mods)
    if dupes:
        print("\n".join([f"Duplicate: {x}. Removed." for x in dupes]))

    modd = statter.mod_metadata(prune_by=mods)

    missing_mod_list = []
    for mod in mods:
        if mod not in source_mods:
            if mod.isnumeric():
                missing_mod_list.append(mod)
            else:
                print(f"Missing mod {mod}, but is not a steam mod")

    if missing_mod_list:
        if click.confirm("Missing mods detected. Download?"):
            print(missing_mod_list)
            modd = downloadMods(missing_mod_list,regen_mods=True)

    dupes = []
    
    pids, dupes = duplicate_check([modd[d]["pid"] for d in modd])

    if dupes:
        print("\n".join([f"Duplicate PID! {x}" for x in dupes]))
        print("Please fix!")
        return    

    link_modlist(mods)

    print("Sorting mods")
    sorter.sorter(get_id_list(instance))

def link_modlist(mods):

    print("Clearing active mod folder")
    empty_folder("active/mods")
    source_mods  = statter.source_mods_list()
    
    for mod in mods:
        try:
            if mod in source_mods:
                os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/mods/{mod}")
            else:
                print(f"Missing Mod. Download failed?: {mod}")
        except FileExistsError:
            print(f"Duplicate Mod: {mod}. This should never happen!")

def downloadMods(mods,regen_mods=False):
    # Pass list of ids
    os.system(f"/home/dormierian/Games/rimworld/SteamCMD/steamcmd.sh +logon anonymous +workshop_download_item 294100 {" +workshop_download_item 294100 ".join(mods)} +exit")
    set_download_time(mods)

    empty_folder("active/fresh/")
    for mod in mods:
        os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/fresh/{mod}")
        # Move fresh mods to a folder to perform operations on

    if click.confirm("\nDDS-encode downloaded mods?"):
        dds_encode("active/fresh")

    # Regenerate the metadata and return the fresh list
    if regen_mods:
        return statter.partial_metadata_regen(mods)
    

def set_download_time(mods, write_time=None):
    if not write_time:
        write_time = str(time.time() * 1000)

    for mod in mods:
        if not os.path.exists(f"source_mods/{mod}/timeDownloaded"):
            open(f"source_mods/{mod}/timeDownloaded","x")
        with open(f"source_mods/{mod}/timeDownloaded",'w') as dateFile:
            dateFile.write(write_time)

def dds_encode(path):
    os.system(f"./todds -f BC1 -af BC7 -on -vf -fs -r Textures -t -p {path}")

def get_id_list(instance):
    mods = []

    with open(f"instances/{instance}/modlist.csv","r") as instance_csv:
        reader = csv.reader(instance_csv)
        for row in reader:
            mods=row
    
    return mods

def search_folders(folder,search):
    results = []
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in dirs:
            if name in search:
                results.append(os.path.join(root, name))
    return results