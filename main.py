#!/home/dormierian/Games/rimman/bin/python

if __name__ != "__main__":
    raise 

import os, click, humanize, regex, csv, time, subprocess
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from logger import Logger as log

from datetime import datetime
# from sheet_manager import get_modlist_info, get_instances, get_slow_mods, push_to_backend, copy_instance_sheet
import mod_handler, rentry, sorter, sheet_manager

from statter import meta, fetch

os.chdir(os.path.dirname(os.path.realpath(__file__)))

@click.group
def cli():
    pass

def modlist_sheet_grab(instance,fetch=None):
    if fetch is None:
        fetch = click.confirm("Get modlist from sheet?")
    if fetch:
        with open(f"instances/{instance}/modlist.csv","w") as instance_csv:
            instance_csv.write(sheet_manager.get_modlist_info(instance))

def prompt_instance_name():
    instance_name = ""
    if os.path.exists(f"cached_instance_name"):
        with open(f"cached_instance_name","r") as instance_cache:
                cached_instance_name = instance_cache.readlines()[0]
        if click.confirm(f"Use cached instance {cached_instance_name}?"):
            instance_name = cached_instance_name
            log().log(f"Using cached instance {instance_name}")
    if not instance_name:
        with open(f"cached_instance_name","w") as instance_cache:            
            instance_name = inquirer.select(
                message="Choose instance",
                choices=sheet_manager.get_instances(),
                pointer=">",
            ).execute()

            instance_cache.write(instance_name)
    return instance_name

@cli.command
def modlist():
    instance_name = prompt_instance_name()    
    modlist_sheet_grab(instance_name)
    mod_handler.generate_modlist(instance_name)

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

@cli.command("stats")
@click.argument("choice",nargs = -1)    
def cli_mods_stats(choice):
    options = ["authors","subscribers","size","time","dependencies","C#"]

    if len(choice) > 1:
        log().log("Please pass 0 or 1 choice")
        return
    elif len(choice) == 0:
        choice = inquirer.select(
            message="Get mods by",
            choices=options,
            pointer=">",
        ).execute()
    else:
        choice = choice[0]
        if choice not in options:
            log().warn("Option not valid")
            return

    if click.confirm("Prune by instance?"):
        modlist = mod_handler.get_id_list(prompt_instance_name())
    else:
        modlist = fetch.source_mods_list()

    if choice == "authors":
        modd = meta.mod_metadata(prune_by=modlist)
        authors = {}
        for d in modd:
            if modd[d]["author"]:
                # Split authors by commas, strip whitespace, and increment mod count for each author

                for author in [x.lstrip() for x in modd[d]["author"].split(",")]:
                    if author in authors:
                        authors[author].append(d)
                    else:
                        authors[author] = [d]

        # Sort authors by the number of mods they made (descending order)
        authors = {k: v for k, v in sorted(authors.items(), key=lambda item: len(item[1]), reverse=True)}

        choices = [Choice(value=author,name=f"{author}: {len(authors[author])} mods") for author in authors]
        author = inquirer.select(
            message="Choose author",
            choices=choices,
            pointer=">",
        ).execute()

        log().log("\n".join([modd[mod]["graphical_name"] for mod in authors[author]]))
    elif choice == "dependencies":
        modd = meta.mod_metadata(include_ludeon=True,prune_by=modlist)
        deps = {}
        
        for d in modd:
            if modd[d]["deps"]:
                for dep in modd[d]["deps"]:
                    if dep in deps:
                        deps[dep].append(d)
                    else:
                        deps[dep] = [d]

        # Sort authors by the number of mods they made (descending order)
        deps = {k: v for k, v in sorted(deps.items(), key=lambda item: len(item[1]), reverse=True)}

        modd_by_pid = {modd[x]["pid"]: modd[x] for x in modd}

        choices = [Choice(value=dep,name=f"{modd_by_pid[dep]["name"] if dep in modd_by_pid else dep} has {len(deps[dep])} dependents") for dep in deps]

        dep = inquirer.select(
            message="Select mod to get dependencies of",
            choices=choices,
            pointer=">",
        ).execute()

        log().log("\n".join(
            [modd[dep]["graphical_name"] for dep in deps[dep]]
        ))
        
    elif choice == "subscribers":
        modd = meta.mod_metadata(sort_by="subs",prune_by=modlist)
        log().log("".join([f"{modd[mod]['graphical_name']} has {modd[mod]['subs']} subscribers \n" for mod in modd]))
    elif choice == "size":
        modd = meta.mod_metadata(sort_by="size",prune_by=modlist)
        log().log("".join([f"{modd[mod]["graphical_name"]} is {humanize.naturalsize(modd[mod]["size"], binary=True)} \n" for mod in modd]))
    elif choice == "time":
        modd = meta.mod_metadata(sort_by="time_created",prune_by=modlist)
        log().log("".join([f"{modd[mod]["graphical_name"]} was made at {datetime.fromtimestamp(int(modd[mod]["time_created"])/1000).strftime('%Y-%m-%d %H:%M:%S')}\n" for mod in modd]))
    elif choice == "C#":
        modd = meta.mod_metadata(sort_by="size",prune_by=modlist)
        log().log("".join([f"{"XML" if modd[mod]["xml_only"] else "C#"}: {modd[mod]["graphical_name"]}\n" for mod in modd]))
        xml_count = len([mod for mod in modd if not modd[mod]["xml_only"]])
        log().log(f"{xml_count}/{len(modlist)} xml mods")

@click.argument("choice",nargs = -1)    
@cli.command("rentry")
def reentry_manager(choice):
    options = ["generate","load","compare","slow_mods"]

    if len(choice) > 1:
        log().log("Please pass 0 or 1 choice")
        return
    elif len(choice) == 0:
        choice = inquirer.select(
            message="Rentry",
            choices=options,
            pointer=">",
        ).execute()
    else:
        choice = choice[0]
        if choice not in options:
            log().warn("Option not valid")
            return

    if choice == "load":
        url = click.prompt("Rentry Url?")
        ren = rentry.import_rentry(url)

        modd = meta.mod_metadata(index_by="pid",include_ludeon=True)
        notin = [x for x in ren if x not in modd]
        log().log("\n Missing Mod: ".join(notin))
    elif choice == "compare":
        url = click.prompt("Rentry Url?")
        ren = rentry.import_rentry(url)

        modd = meta.mod_metadata(index_by="pid",include_ludeon=True,prune_by=sheet_manager.get_modlist_info(prompt_instance_name()))
        yesin = [modd[x]["name"] for x in ren if x in modd]
        log().log("\n".join(yesin))     
    elif choice == "generate":
        instance_name = prompt_instance_name()
        mods = mod_handler.get_id_list(instance_name)
        modd = meta.mod_metadata(prune_by=mods,index_by="pid",include_ludeon=True)
        
        i = 0
        for mod in sorter.sorter(mods):
            i+=1
            modd[mod]["sort"] = i
        start_time = time.time()
        ren = rentry.compile_rentry(modd)
        log().info(f"Generated rentry for {i} mods in {time.time()-start_time}")

        start_time = time.time()
        # with open("temp","w") as f:
        #     f.write(ren)
        rentry.upload(ren)
        log().info(f"Uploaded in {time.time()-start_time}")

    elif choice == "check for slow mods":
        url = click.prompt("Rentry Url?")
        modlist = rentry.import_rentry(url)
        slow_mods = sheet_manager.get_slow_mods()

        log().info([x for x in modlist if x in slow_mods])

@cli.command("encode")
def encode():
    mod_handler.dds_encode("source_mods")

@cli.command("modd")
def cli_modd():
    meta.mod_metadata(regen=True)

@cli.command("sheet_push")
def sheet_push(instance_name=None):
    if not instance_name:
        instance_name = prompt_instance_name()
    instance = mod_handler.get_id_list(instance_name)
    modd = meta.mod_metadata(sort_by="time_first_downloaded") 
    sheet_manager.push_to_backend(modd,instance,instance_name)

@cli.command("time")
def whenlastupdated():
    time = click.prompt("Time to set (unix milis)")
    mod_handler.set_download_time(fetch.source_mods_list(steam_only=True),time)
    Path("data/modd_dirty").touch()

@cli.command("sort")
def cli_sort_modlist():
    sorter.sorter(mod_handler.get_id_list(prompt_instance_name()))

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
        instance_name = prompt_instance_name()
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
        source = prompt_instance_name()
    else:
        source = "Instance Template"
    
    if sheet_manager.copy_instance_sheet(source,instance_name):
        log().log("Sheet copied")
    else:
        log().warn("Sheet already exists!")
    
    os.mkdir("instances/"+instance_name)

    with open(f"instances/{instance_name}/modlist.csv","w") as f:
        f.write(sheet_manager.get_modlist_info(instance_name))   

@cli.command("inscon")
@click.argument("instance",nargs = -1)
def cli_manage_instance(instance):
    if len(instance) > 1:
        log().log("Please pass 0 or 1 instance")
        return
    elif len(instance) == 0:
        instance = prompt_instance_name()
    else:
        instance = instance[0]
    
    modd = meta.mod_metadata(sort_by="time_first_downloaded")

    modlist_sheet_grab(instance)
    instance_list = mod_handler.get_id_list(instance)

    choices = [
        Choice(name=modd[d]["name"],value=d,enabled=d in instance_list) 
        for d in modd
    ]

    response = inquirer.select(
        message="Select which mods to toggle",
        choices=choices,
        pointer=">",
        multiselect=True
    ).execute()

    to_enable = [mod for mod in response if mod not in instance_list]

    to_disable = [mod for mod in instance_list if mod not in response]

if __name__ == '__main__':
    cli()
