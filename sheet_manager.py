import gspread, os
from dotenv import load_dotenv

load_dotenv()

def get_spreadsheet():
    gc = gspread.service_account(filename='data/service_account.json')
    return gc.open_by_key(os.getenv("SPREADSHEET"))

def get_modlist_info(instance):
    sh = get_spreadsheet()
    instance_sheet = sh.worksheet(instance)
    return instance_sheet.acell("E2").value

def get_instances():
    sh = get_spreadsheet()
    sheets = [sheet.title for sheet in sh.worksheets()]
    
    unwanted = ["Mods","SlowModsComparer","ModlistComparer","Instance Template","Backend"]
    sheets = [sheet for sheet in sheets if sheet not in unwanted ]

    return sheets

def set_sorder(sorder,instance):    
    sh = get_spreadsheet()
    ws = sh.worksheet(instance)

    mids = ws.col_values(3)
    mids.pop()

    sorder_range = [None] * (len(mids))

    i = 0
    for mid in mids:
        if mid in sorder:
            sorder_range[i] = sorder[mid]
        i+=1
    
    sorder_range = [[x] for x in sorder_range]

    ws.update(sorder_range,"D:D")

    print(sorder_range)