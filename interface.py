import click, os, statter.sheet_manager
from InquirerPy import inquirer

from logger import Logger as log

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
                choices=statter.sheet_manager.get_instances(),
                pointer=">",
            ).execute()

            instance_cache.write(instance_name)
    return instance_name