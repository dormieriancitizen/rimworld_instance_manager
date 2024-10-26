import click, time
import interface, sorter, rentry

from pathlib import Path

from InquirerPy.base.control import Choice
from InquirerPy import inquirer

from logger import Logger as log

from mod_handler import generate_modlist
from statter import fetch, meta, sheet_manager

@click.group()
def instance():
    pass

@click.argument("instance",nargs = -1)
@instance.command("list")
def modlist(instance):
    if len(instance) == 1:
        instance = instance[0]
    else:
        instance = interface.prompt_instance_name()

    generate_modlist(fetch.get_modlist(instance))

@instance.command("sort")
def cli_sort_modlist():
    sorter.sorter(fetch.get_modlist(interface.prompt_instance_name()))

@instance.command("control")
@click.argument("instance",nargs = -1)
def cli_manage_instance(instance):
    if len(instance) > 1:
        log().log("Please pass 0 or 1 instance")
        return
    elif len(instance) == 0:
        instance = interface.prompt_instance_name()
    else:
        instance = instance[0]
    
    modd = meta.parse_modd(meta.mod_metadata(),sort_by="time_first_downloaded")

    
    instance_list = fetch.get_modlist(instance)

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

@instance.group("rentry")
def reentry_manager():
    pass

    # url = click.prompt("Rentry Url?")
    # modlist = rentry.import_rentry(url)
    # slow_mods = sheet_manager.get_slow_mods()

    # log().info([x for x in modlist if x in slow_mods])

@reentry_manager.command("generate")
def rentry_generate():
    mods = fetch.get_modlist(interface.prompt_instance_name(),fetch=False)
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


@reentry_manager.command("generate_from_xml")
def rentry_generate():
    path = Path("/home/dormierian/Downloads/mods.xml")

    modlist = fetch.get_mods_from_modsconfig(path)

    modd = meta.parse_modd(meta.mod_metadata(include_ludeon=True),index_by="pid")

    missing_mods = [mod for mod in modlist if not mod in modd]

    community_rules = fetch.fetch_rimsort_community_rules()["rules"]


    rimsort_pid_names = {}
    for pid in community_rules:
        if "loadBefore" in community_rules[pid]:
            rimsort_pid_names.update(community_rules[pid]["loadBefore"])
        if "loadAfter" in community_rules[pid]:
            rimsort_pid_names.update(community_rules[pid]["loadAfter"])    

    pids_by_name = {}
    for pid in rimsort_pid_names:
        if "name" in rimsort_pid_names[pid]:
            name = rimsort_pid_names[pid]["name"]

            if isinstance(name,list):
                name = name[0]

            if name:
                pids_by_name[pid] = name

    if missing_mods:
        for mod in missing_mods:
            modd[mod] = {
                "pid": mod,
                "xml_only": False,
                "source": "LOCAL",
                "name": pids_by_name[mod] if mod in pids_by_name else mod,
                "download_link": "",
            }

    i = 0
    for mod in modlist:
        i+=1
        modd[mod]["sort"] = i

    modd = {pid: modd[pid] for pid in modd if pid in modlist}

    start_time = time.time()
    ren = rentry.compile_rentry(modd)
    log().info(f"Generated rentry for {i} mods in {time.time()-start_time}")

    start_time = time.time()
    # with open("temp","w") as f:
    #     f.write(ren)
    rentry.upload(ren)
    log().info(f"Uploaded in {time.time()-start_time}")

@reentry_manager.command("missing")
def rentry_missing():
    ren = rentry.import_rentry(click.prompt("Rentry Url?"))

    modd = meta.mod_metadata(
        index_by="pid",
        include_ludeon=True,
        prune_by=sheet_manager.get_modlist_info(interface.prompt_instance_name())
    )

    missing_mods = [modd[x]["name"] for x in ren if x not in modd]
    log().log("\n".join(missing_mods))