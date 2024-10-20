import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

import interface
from logger import Logger as log

from mod_handler import generate_modlist
from statter import fetch, meta

import humanize
from datetime import datetime

@click.group(invoke_without_command=True)
@click.argument("choice",nargs = -1)    
def stats(choice):
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
        modlist = fetch.get_modlist(interface.prompt_instance_name(),fetch=False)
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