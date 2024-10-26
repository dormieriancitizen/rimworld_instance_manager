import click
import interface, sorter

from InquirerPy.base.control import Choice
from InquirerPy import inquirer

from logger import Logger as log

from mod_handler import generate_modlist
from statter import fetch, meta

from commands.rentry import reentry_manager

@click.group()
def instance():
    pass

instance.add_command(reentry_manager)

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
