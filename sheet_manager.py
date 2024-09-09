import gspread, os
from dotenv import load_dotenv

load_dotenv()

def get_spreadsheet():
    gc = gspread.service_account(filename='service_account.json')
    return gc.open_by_key(os.getenv("SPREADSHEET"))

def get_modlist_info(instance):
    sh = get_spreadsheet()
    instance_sheet = sh.worksheet(instance)
    return instance_sheet.acell("E2").value

def get_instances():
    sh = get_spreadsheet()
    sheets = [sheet.title for sheet in sh.worksheets()]
    
    unwanted = ["Mods","SlowModsComparer","ModlistComparer","Instance Template"]
    sheets = [sheet for sheet in sheets if sheet not in unwanted ]

    return sheets