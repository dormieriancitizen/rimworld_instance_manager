import subprocess, json

def fetch_rimsort_community_rules():
    subprocess.Popen("git -C data/rs_rules pull",shell=True,stdout=subprocess.DEVNULL).wait()
    with open("data/rs_rules/communityRules.json", "r") as f:
        return json.load(f)
    
def rimsort_pid_names():
    community_rules = fetch_rimsort_community_rules()

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
    
    return pids_by_name