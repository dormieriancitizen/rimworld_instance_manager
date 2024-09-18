import gspread, os
from dotenv import load_dotenv

load_dotenv()

def get_spreadsheet():
    gc = gspread.service_account(filename='data/service_account.json')
    return gc.open_by_key(os.getenv("SPREADSHEET"))

def get_modlist_info(instance):
    sh = get_spreadsheet()
    instance_sheet = sh.worksheet(instance)
    return instance_sheet.acell("H2").value

def get_instances():
    sh = get_spreadsheet()
    sheets = [sheet.title for sheet in sh.worksheets()]
    
    unwanted = ["Mods","Instance Template",]
    sheets = [sheet for sheet in sheets if sheet not in unwanted ]

    return sheets

def get_slow_mods():
    gc = gspread.service_account(filename='data/service_account.json')
    sh = gc.open_by_key("14xvMkf9zo1EjMMNkRNCWoE8QWVHQWd11v69tuyXT10A")
    slow_mods = sh.worksheet("Slow Mods").col_values(2)
    slow_mods.pop()
    return slow_mods

def push_to_backend(modd, instance, instance_name):
    to_push = []
    to_push.append(["id","pid","source","download_link","name","On/Off"])
    for x in modd:
        d = modd[x]
        mod = [
            d["id"],
            d["pid"],
            d["source"],
            d["download_link"],
            d["name"],
            1 if x in instance else 0,
        ]
        to_push.append(mod)
    sh = get_spreadsheet()
    ws = sh.worksheet(instance_name)
    ws.update(to_push,"A:F")