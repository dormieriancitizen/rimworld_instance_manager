
import click, requests, json, time, subprocess, os
from colorama import Style

def fetch_steam_info(fetch=None,mods=None):
    if not fetch:
        fetch = click.confirm("Fetch new mod info?")
    if fetch:
        start_time = time.time()

        # Read from the steam API and write to file
        if not mods:
            mods = source_mods_list(steam_only=True)

        url = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        
        # # Construct the publishedfileids parameter
        # publishedfileids = "&".join(f"publishedfileids%5B{i}%5D={mod_id}" for i, mod_id in enumerate(source_mods))
        
        # # Construct the final URL
        # url = f"https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/?itemcount={len(source_mods)}&{publishedfileids}"

        payload = {"itemcount": len(mods)}
        for i in range(len(mods)):
            payload[f"publishedfileids[{i}]"] = mods[i]

        steamd = requests.post(url, data=payload).json()
        
        if not mods:
            responseFile = open("data/response.json","w")
            json.dump(steamd, responseFile)
            responseFile.close()

        print(f"{Style.DIM}Fetched from steam in {time.time()-start_time}{Style.RESET_ALL}")
    else:
        with open("data/response.json", "r") as f:
            steamd = json.load(f)
    
    # Reorganise the response by each ID
    steamd = {mod["publishedfileid"]: mod for mod in steamd["response"]["publishedfiledetails"]}

    return steamd


def fetch_rimsort_community_rules():
    subprocess.Popen("git -C data/rs_rules pull",shell=True,stdout=subprocess.DEVNULL).wait()
    with open("data/rs_rules/communityRules.json", "r") as f:
        return json.load(f)
    

def source_mods_list(steam_only=None):
    source_mods = [f.path.split("/", 1)[1] for f in os.scandir("source_mods") if f.is_dir()]
    if steam_only:
        source_mods = [f for f in source_mods if f.isnumeric()]
    return source_mods