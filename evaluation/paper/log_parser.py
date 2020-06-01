#! /usr/bin/env python3

import os
import json

from typing import Dict, Tuple, Any, List


# folder containing all the experiment data
DATA_PATH = "/research_data/sommer2020cadr/"


def load_simulation(path: str) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Loads a single experiment's data"""
    simId: str = ""
    params = {}
    logs: Dict[str, List[Dict[str, Any]]] = {}

    for dirpath, _, files in os.walk(path):
        for file in files:
            if "dtnd_run.log" in file:
                node_name: str = file.split("_")[0].split(".")[0]
                node_logs: List[Dict[str, Any]] = []
                print(f"Parsing {file}")
                with open(os.path.join(dirpath, file), "r") as f:
                    for line in f:
                        content: Dict[str, Any] = json.loads(line)
                        node_logs.append(content)
                logs[node_name] = node_logs

            elif "parameters.py" == file:
                with open(os.path.join(dirpath, file), "r") as f:
                    # I don't know any better way to do this
                    # I tried executing the code with exec() and then accessing the assigned variables
                    # but that doesn't work. Probably because of some namespacing issue...
                    # (I can see the variables with the correct values in the debugger, but I can't access them in code
                    for line in f:
                        if "params =" in line:
                            pseudo_json = line.split("=")[1].strip().replace("'", '"')
                            params = json.loads(pseudo_json)
                            simId = params["simId"]

    return simId, {"params": params, "logs": logs}


def load_all(path: str) -> Dict[str, Dict[str, Any]]:
    """Load the data of all experiments"""
    runs: Dict[str, Dict[str, Any]] = {}
    for experiment in os.listdir(path):
        simId, data = load_simulation(path=os.path.join(path, experiment))
        runs[simId] = data
    return runs


if __name__ == "__main__":
    load_all(path=DATA_PATH)
