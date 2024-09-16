import statter, click, os, csv, time
from helpers import *

from sheet_manager import set_sorder

def generateModList(instance):
    mods = getIdList(instance)

    print("Clearing active mod folder")
    empty_folder("active/mods")
    source_mods  = statter.source_mods_list()
    # print(source_mods)

    missing_mod_list = []

    for mod in mods:
        if mod in source_mods:
            continue
        else:
            print(f"Missing Mod: {mod}")
            missing_mod_list.append(mod)
    
    if missing_mod_list:
        if click.confirm("Missing mods detected. Try to download?"):
            downloadMods(missing_mod_list)
        generateModList(instance)
    else:
        for mod in mods:
            try:
                if mod in source_mods:
                    os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/mods/{mod}")
                else:
                    print(f"Missing Mod. Download failed?: {mod}")
            except FileExistsError:
                print(f"Duplicate Mod: {mod}")
        if click.confirm("Run RimPy?"):
            os.chdir("../rimpy/")
            os.system("./rimpy")

def downloadMods(mods):
    # Pass list of ids
    os.system(f"/home/dormierian/Games/rimworld/SteamCMD/steamcmd.sh +logon anonymous +workshop_download_item 294100 {" +workshop_download_item 294100 ".join(mods)} +exit")
    setDownloadTime(mods)

    empty_folder("active/fresh/")
    for mod in mods:
        os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/fresh/{mod}")
        # Move fresh mods to a folder to perform operations on
    
    extra_folders = search_folders("active/fresh",[".git","obj"])
    if extra_folders:
        if click.confirm("Detected some extraneous folders, delete them?"):
            deleted_size = sum([du(x) for x in extra_folders])
            for folder in extra_folders:
                empty_folder(folder)
            print(f"Deleted {deleted_size} bytes of extra stuff")

    if click.confirm("\nDDS-encode downloaded mods?"):
        ddsEncode("active/fresh")
    

def setDownloadTime(mods, write_time=None):
    if not write_time:
        write_time = str(time.time() * 1000)

    for mod in mods:
        if not os.path.exists(f"source_mods/{mod}/timeDownloaded"):
            open(f"source_mods/{mod}/timeDownloaded","x")
        with open(f"source_mods/{mod}/timeDownloaded",'w') as dateFile:
            dateFile.write(write_time)

def ddsEncode(path):
    os.system(f"./todds -f BC1 -af BC7 -on -vf -fs -r Textures -t -p {path}")

def getIdList(instance):
    mods = []

    with open(f"instances/{instance}/modlist.csv","r") as instance_csv:
        reader = csv.reader(instance_csv)
        for row in reader:
            mods=row
    
    return mods

def load_sorder_to_sheet(instance_name):
    sorder = statter.load_sort_order(getIdList(instance_name))

    set_sorder(sorder,instance_name)

def search_folders(folder,search):
    results = []
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in dirs:
            if name in search:
                results.append(os.path.join(root, name))
    return results