#!/home/dormierian/Games/rimman/venv/bin/python

if __name__ != "__main__":
    raise 

import os, click, regex, csv, subprocess
from pathlib import Path

from logger import Logger as log

import mod_handler, interface
from statter import meta, fetch, sheet_manager

from commands import modlist, stats

os.chdir(os.path.dirname(os.path.realpath(__file__)))

@click.group
def cli():
    pass

cli.add_command(modlist.instance)
cli.add_command(stats.stats)

@cli.command("update")
def cli_update():
    modd = meta.mod_metadata(always_prompt=True)
    to_update = {}

    for mod in modd:
        if modd[mod]["source"] == "STEAM":
            timeDownloaded = modd[mod]["time_downloaded"]
            timeUpdated = modd[mod]["time_updated"]
            if timeDownloaded < timeUpdated:
                log().log(f"STEAM mod {modd[mod]["graphical_name"]} is out of date.")
                to_update[mod] = {}
                to_update[mod]["source"] = "STEAM"
        if modd[mod]["source"] == "GIT":
            process = subprocess.Popen(f"git -C source_mods/{mod} pull", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            # Decode the output from bytes to string
            stdout = stdout.decode('utf-8')
            if "Already up to date" not in stdout:
                log().log(f"GIT mod {modd[mod]["graphical_name"]} has been updated.")
                # to_update[mod] = {"source": "GIT"}

    log().info(f"{len(to_update)} mods were out of date")

    if to_update:
        if click.confirm("Download steam mods now?"):
            mod_handler.downloadMods(to_update,regen_mods=False)
    else:
        log().log("No mods detected out of date.")

@cli.command("encode")
def encode():
    mod_handler.dds_encode("source_mods")

@cli.command("modd")
def cli_modd():
    meta.mod_metadata(regen=True)

@cli.command("sheet_push")
def sheet_push(instance_name=None):
    if not instance_name:
        instance_name = interface.prompt_instance_name()
    instance = fetch.get_modlist(instance_name,fetch=False)
    modd = meta.parse_modd(meta.mod_metadata(),sort_by="time_first_downloaded") 
    sheet_manager.push_to_backend(modd,instance,instance_name)

@cli.command("time")
def whenlastupdated():
    time = click.prompt("Time to set (unix milis)")
    mod_handler.set_download_time(fetch.source_mods_list(steam_only=True),time)
    Path("data/modd_dirty").touch()

@cli.command("add_mods")
def cli_add_mods():
    modd = meta.mod_metadata()
    to_download = {}

    os.system("micro active/mods_to_add.txt")

    with open("active/mods_to_add.txt", "r") as f:
        for line in f:
            if "steamcommunity.com" in line:
                id_match = regex.search(r"(?<=\?id=)([0-9]*)",line)
                if id_match:
                    mod_id = id_match.group()
                    if mod_id in modd or mod_id in to_download:
                        log().warn(f"{mod_id} already downloaded or in buffer")
                        continue
                    to_download[mod_id] = {"source": "STEAM"}
                else:
                    log().warn("Couldn't get id, try again")
                    continue
            if "github.com" in line:
                mod_id = regex.search(r"(?<=https://github.com/.*?/)(.*)(?=/)",line)

                if mod_id:
                    mod_id = mod_id.group()
                else:
                    log().warn(f"Didn't match anything in {line}")
                    continue

                if mod_id in modd or mod_id in to_download:
                        log().warn(f"{mod_id} already downloaded or in buffer")

                to_download[mod_id] = {"source": "GITHUB", "download_link": line}

    modd = mod_handler.downloadMods(to_download, regen_mods=True)

    if click.confirm("Add fresh mods to instance?"):
        instance_name = interface.prompt_instance_name()
        with open(f"instances/{instance_name}/modlist.csv","r") as instance_csv:
            reader = csv.reader(instance_csv)
            for row in reader:
                mods=row
        mods.extend(to_download.keys())
        with open(f"instances/{instance_name}/modlist.csv","w") as instance_csv:
            instance_csv.write(",".join(mods))
        sheet_manager.push_to_backend(modd,mods,instance_name)
    mods = []
    
    return mods

@cli.command("mkinstance")
def cli_make_instance():
    instance_name = click.prompt("What do you want to name the instance?")

    if click.confirm("Copy existing instance?"):
        source = interface.prompt_instance_name()
    else:
        source = "Instance Template"
    
    if sheet_manager.copy_instance_sheet(source,instance_name):
        log().log("Sheet copied")
    else:
        log().warn("Sheet already exists!")
    
    os.mkdir("instances/"+instance_name)

    with open(f"instances/{instance_name}/modlist.csv","w") as f:
        f.write(sheet_manager.get_modlist_info(instance_name))   

if __name__ == '__main__':
    cli()
