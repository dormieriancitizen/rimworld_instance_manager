import click, os, csv, time, subprocess, regex, asyncio

from pathlib import Path
import sorter

from logger import Logger as log

from statter import meta, fetch

def unlink_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path):
            #     shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def duplicate_check(tocheck):
    nodupes = []
    dupes = []
    for check in tocheck:
        if check not in nodupes:
            nodupes.append(check)
        else:
            dupes.append(check)
    check = nodupes
    return nodupes, dupes

def generate_modlist(mods):
    def remove_duplicate_ids(mods):
        mods, dupes = duplicate_check(mods)
        if dupes:
            log().warn("\n".join([f"Duplicate: {x}. Removed." for x in dupes]))
        return mods
    def check_deps(mods,modd):
        modd_by_pid = meta.parse_modd(modd,index_by="pid",prune_by=mods)
        all_modd_by_pid = meta.parse_modd(modd,index_by="pid")

        for d in modd_by_pid:
            for dep in modd_by_pid[d]["deps"]:
                if dep.startswith("ludeon."):
                    continue
                if not dep in modd_by_pid:
                    if dep in all_modd_by_pid:
                        if all_modd_by_pid[dep]["id"] not in mods:
                            log().warn(f"{modd[d]["graphical_name"]} depends on {dep}, but is a known PID. Adding to modlist")
                            mods.append(all_modd_by_pid[dep]["id"])
                    else:
                        log().error(f"Missing unknown dependency {dep}")
        return mods
    def validate_mods_present(mods):
        source_mods  = fetch.source_mods_list()
        missing_modlist = []
        for mod in mods:
            if mod not in source_mods:
                if fetch.is_steam_mod(mod):
                    missing_modlist.append(mod)
                else:
                    missing_modlist.append(mod)
                    log().warn(f"Missing mod {mod}, but is not a steam mod")
        return missing_modlist    

    log().log(f"Parsing modlist for {len(mods)} mods")

    mods = remove_duplicate_ids(mods)

    modd = meta.mod_metadata()
    missing_modlist = validate_mods_present(mods)

    if missing_modlist:
        log().error("Missing mods detected. Add then using rimman add_mods")
        log().error(missing_modlist)
        return

    pids, dupes = duplicate_check(meta.parse_modd(modd,prune_by=mods,index_by="pid"))

    if dupes:
        log().error("\n".join([f"Duplicate PID! {x}" for x in dupes])+"\nPlease fix!")
        raise Exception("Duplicate PIDS")    

    check_deps(mods,modd)

    log().log(f"Modlist Length: {len(mods)}")
    link_modlist(mods)

    log().log("Sorting mods")
    order = sorter.sorter(mods)

    with open(Path.home() / ".config" /"unity3d" / "Ludeon Studios" / "RimWorld by Ludeon Studios" / "Config" / "ModsConfig.xml","w") as f:
        f.write(sorter.generate_modconfig_file(order))

def link_modlist(mods):
    log().info("Clearing active mod folder")
    unlink_folder("active/mods")
    source_mods  = fetch.source_mods_list()
    
    for mod in mods:
        try:
            if mod in source_mods:
                os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/mods/{mod}")
            else:
                log().warn(f"Missing Mod. Download failed?: {mod}")
        except FileExistsError:
            log().error(f"Duplicate Mod: {mod}. This should never happen!")

def downloadMods(mods,regen_mods=False):
    # pattern = r"(?<=https://github.com/.*?/)(.*)(?=/)"
    # mods = [regex.search(pattern, url).group(1) if regex.search(pattern, url) else None for url in github_mods]

    steam_mods = [mod for mod in mods if mods[mod]["source"]=="STEAM"]
    github_mods = [mods[mod]["download_link"] for mod in mods if mods[mod]["source"]=="GIT"]

    dls = []

    if steam_mods:
        # Pass list of ids
        command = [
            "/home/dormierian/Games/rimworld/SteamCMD/steamcmd.sh",
            "+logon", "anonymous",
        ]

        # Add each mod ID to the command
        for mod in steam_mods:
            command.extend(["+workshop_download_item", "294100", mod])

        command.append("+exit")

        # Execute the command
        dls.append(subprocess.Popen(' '.join(command), shell=True))
    
    if github_mods:
        for mod in github_mods:
            command = " ".join(["git","-C", "source_mods/", "clone", mod])
            dls.append(subprocess.Popen(command, shell=True))
    
    [dl.wait() for dl in dls]

    set_download_time(mods)

    unlink_folder("active/fresh/")
    for mod in mods:
        os.symlink(os.path.abspath(f"source_mods/{mod}"),f"active/fresh/{mod}")
        # Move fresh mods to a folder to perform operations on

    if click.confirm("\nDDS-encode downloaded mods?"):
        encodes = []
        for mod in mods:
            encodes.append(dds_encode(f"active/fresh/{mod}"))
        [encode.wait() for encode in encodes]

    # Regenerate the metadata and return the fresh list
    if regen_mods:
        return asyncio.run(meta.gen_mod_metadata(mods=steam_mods,steam_fetch=True))
    

def set_download_time(mods, write_time=None):
    if not write_time:
        write_time = str(time.time() * 1000)

    for mod in mods:
        if not os.path.exists(f"source_mods/{mod}/time_initially_downloaded"):
            with open(f"source_mods/{mod}/time_initially_downloaded","w") as dateFile:
                dateFile.write(write_time)
        with open(f"source_mods/{mod}/timeDownloaded",'w') as dateFile:
            dateFile.write(write_time)

def dds_encode(path):
    return subprocess.Popen(f"./todds -f BC1 -af BC7 -on -vf -fs -r Textures -t -p {path}",shell=True)

def search_folders(folder,search):
    results = []
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in dirs:
            if name in search:
                results.append(os.path.join(root, name))
    return results