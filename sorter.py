from collections import Counter

from logger import Logger as log
from statter import meta

def find_circular_dependencies(nodes):
    def dfs(node, visited, rec_stack, path, cycles):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Explore all the neighbors of the current node
        for neighbor in nodes.get(node, []):
            if neighbor not in visited:
                # If not visited, do DFS on this neighbor
                dfs(neighbor, visited, rec_stack, path, cycles)
            elif neighbor in rec_stack:
                # If the neighbor is in the current recursion stack, a cycle is found
                cycle_start_idx = path.index(neighbor)
                cycle = path[cycle_start_idx:] + [neighbor]
                cycles.append(cycle)
        
        # Remove the node from the recursion stack before backtracking
        rec_stack.remove(node)
        path.pop()

    visited = set()
    rec_stack = set()
    cycles = []
    
    # Check each node to ensure we don't miss any disconnected parts of the graph
    for node in nodes:
        if node not in visited:
            dfs(node, visited, rec_stack, [], cycles)

    if cycles:
        for cycle in cycles:
            log().error(f"Circular dependency detected: {' -> '.join(cycle)}")

def topological_sort(nodes,modd):
    """
    Topological sort for a network of nodes

        nodes = {"A": ["B", "C"], "B": [], "C": ["B"]}
        topological_sort(nodes)
        # ["A", "C", "B"]

    :param nodes: Nodes of the network
    :return: nodes in topological order
    """

    # Calculate the indegree for each node
    indegrees = {k: 0 for k in nodes.keys()}
    for name, dependencies in nodes.items():
        for dependency in dependencies:
            indegrees[dependency] += 1

    # Place all elements with indegree 0 in queue
    queue = [k for k in nodes.keys() if indegrees[k] == 0]
    # Sort queue alphabetically

    final_order = []

    # Continue until all nodes have been dealt with
    while len(queue) > 0:
        # Sort the queue alphabetically by real name
        queue = sorted(queue,key=lambda x: modd[x]['name'] if 'name' in modd[x] else x,reverse=True)

        # node of current iteration is the first one from the queue
        curr = queue.pop(0)
        final_order.append(curr)

        # remove the current node from other dependencies
        for dependency in nodes[curr]:
            indegrees[dependency] -= 1

            if indegrees[dependency] == 0:
                queue.append(dependency)
        

    # check for circular dependencies
    if len(final_order) != len(nodes):
        log().error("Found circular dependencies.")
        find_circular_dependencies(nodes)
        raise Exception("Circular dependency found.")
    
    # Reverse the list since we have it in reverse order
    final_order.reverse()

    if "krkr.rocketman" in final_order:
        # RocketMan needs to go at the end of a sort order
        final_order.append(final_order.pop(final_order.index('krkr.rocketman')))

    return final_order

def sorter(modlist):
    modd = meta.instance_metadata(modlist)

    # Convert all loadAfter into loadBefore
    for d in modd:
        if not "orderAfter" in modd[d]: 
            modd[d]["orderAfter"] = []
        if modd[d]["loadBefore"]:
            for mod in modd[d]["loadBefore"]:
                if mod in modd:
                    if "orderAfter" not in modd[mod]: 
                        modd[mod]["orderAfter"] = []
                    modd[mod]["orderAfter"].append(d)
        if modd[d]["loadAfter"]:
            modd[d]["orderAfter"].extend([x for x in modd[d]["loadAfter"] if x in modd])

    for d in modd:
        # If not otherwise specified, give every mod an orderAfter Core.
        if d not in modd["ludeon.rimworld"]["orderAfter"]:
            if "ludeon.rimworld" not in modd[d]["orderAfter"]:
                if d != "ludeon.rimworld":
                    modd[d]["orderAfter"].append("ludeon.rimworld")
        
                    # If not otherwise specified, also give every mod an orderAfter all DLCs.
                    dlc_names = ("biotech", "ideology", "royalty", "anomaly")
                    dlc_names = [f"ludeon.rimworld.{dlc_name}" for dlc_name in dlc_names]
                    
                    if d not in [item for sublist in [modd[dlc_name]["orderAfter"] for dlc_name in dlc_names] for item in sublist]:
                        if not Counter(dlc_names) & Counter(modd[d]["orderAfter"]):
                            if not d.startswith("ludeon.rimworld"):
                                modd[d]["orderAfter"].extend(dlc_names)

    deplist = {x: modd[x]["orderAfter"] for x in modd}

    order = topological_sort(deplist,modd)

    return order


def generate_modconfig_file(order):
    c = """<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
    <version>1.5.4104 rev435</version>
    <activeMods>"""
    c += "\n"+"\n".join([f"        <li>{pid}</li>" for pid in order])+"\n"
    c += """    </activeMods>
    <knownExpansions>
        <li>ludeon.rimworld</li>
        <li>ludeon.rimworld.royalty</li>
        <li>ludeon.rimworld.ideology</li>
        <li>ludeon.rimworld.biotech</li>
        <li>ludeon.rimworld.anomaly</li>
    </knownExpansions>
</ModsConfigData>"""
    return c
