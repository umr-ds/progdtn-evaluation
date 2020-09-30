import json
import glob
import os

from typing import Dict, List, Union, Tuple, Set
from datetime import datetime
from graphviz import Digraph

INSTANCE_PATH = "/research_data/final/ids/36"
GRAPH_PATH = "/research_data/final/graphs"


def parse_instance_parameters(path: str) -> Dict[str, Union[str, int]]:
    params: Dict[str, Union[str, int]] = {}
    with open(path, "r") as f:
        # I don't know any better way to do this
        # I tried executing the code with exec() and then accessing the assigned variables
        # but that doesn't work. Probably because of some namespacing issue...
        # (I can see the variables with the correct values in the debugger, but I can't access them in code
        for line in f:
            if "params =" in line:
                pseudo_json = line.split("=")[1].strip().replace("'", '"')
                params = json.loads(pseudo_json)
    return params


def log_entry_time(log_entry):
    return datetime.strptime(log_entry["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")


def parse_node(
    node_path: str, routing_algorithm: str, sim_instance_id: str
) -> Tuple[
    Set[str],
    Dict[str, Dict[str, Union[str, datetime]]],
    Dict[str, List[Dict[str, Union[str, datetime]]]],
]:
    bundles: Set[str] = set()
    creations: Dict[str, Dict[str, Union[str, datetime]]] = {}
    forwards: Dict[str, List[Dict[str, Union[str, datetime]]]] = {}
    node_id = node_path.split("/")[-1].split(".")[0]

    with open(node_path, "r") as f:
        for line in f.readlines():
            try:
                entry = json.loads(line)
                if entry["msg"] == "REST client sent bundle":  # A bundle is created
                    bundles.add(entry["bundle"])
                    creations[entry["bundle"]] = {
                        "routing": routing_algorithm,
                        "sim_instance_id": sim_instance_id,
                        "timestamp": log_entry_time(entry),
                        "node": node_id,
                        "bundle": entry["bundle"],
                    }

                elif (
                    entry["msg"] == "Sending bundle to a CLA (ConvergenceSender)"
                ):  # A bundle is about to be sent
                    endpoint = entry["cla"]["EndpointType"]
                    if endpoint:
                        peer = endpoint["Ssp"].replace("/", "")
                        bundle_forwards = forwards.get(entry["bundle"], [])
                        bundle_forwards.append(
                            {
                                "routing": routing_algorithm,
                                "sim_instance_id": sim_instance_id,
                                "timestamp": log_entry_time(entry),
                                "node": node_id,
                                "bundle": entry["bundle"],
                                "peer": peer,
                            }
                        )
                        forwards[entry["bundle"]] = bundle_forwards

            except json.JSONDecodeError as err:
                print(f"Json parsing error: {err}")

    return bundles, creations, forwards


def instance_chains(
    instance_path: str,
) -> Tuple[
    Set[str],
    Dict[str, Dict[str, Union[str, datetime]]],
    Dict[str, List[Dict[str, Union[str, datetime]]]],
]:
    node_paths: List[str] = glob.glob(
        os.path.join(instance_path, "*.conf_dtnd_run.log")
    )
    param_path: str = os.path.join(instance_path, "parameters.py")
    params: Dict[str, Union[str, int]] = parse_instance_parameters(path=param_path)

    bundles: Set[str] = set()
    creations: Dict[str, Dict[str, Union[str, datetime]]] = {}
    forwards: Dict[str, List[Dict[str, Union[str, datetime]]]] = {}
    for node_path in node_paths:
        node_bundles, node_creations, node_forwards = parse_node(
            node_path=node_path,
            routing_algorithm=params["routing"],
            sim_instance_id=params["simInstanceId"],
        )
        bundles = bundles.union(node_bundles)
        creations = {**creations, **node_creations}
        for bundle in node_bundles:
            bundle_forwards = forwards.get(bundle, [])
            bundle_forwards += node_forwards.get(bundle, [])
            forwards[bundle] = bundle_forwards

    return bundles, creations, forwards


def dump_graph(
    output_folder: str,
    bundles: Set[str],
    creations: Dict[str, Dict[str, Union[str, datetime]]],
    forwards: Dict[str, List[Dict[str, Union[str, datetime]]]],
) -> None:
    for bundle in bundles:
        safe_bundle_name = bundle.replace(":", "").replace("/", "")
        out_source = f"{safe_bundle_name}.dot"
        dot = Digraph(comment=f"Bundle: {bundle}")
        dot.node("S", "Creation")
        dot.node(creations[bundle]["node"])
        dot.edge("S", creations[bundle]["node"])

        nodes: Set[str] = set()
        for forward in forwards[bundle]:
            sender = forward["node"]
            nodes.add(sender)
            recipient = forward["peer"]
            nodes.add(recipient)
            dot.edge(sender, recipient)

        for node in nodes:
            dot.node(node)

        with open(os.path.join(output_folder, out_source), "w") as f:
            f.write(dot.source)

        dot.render(os.path.join(output_folder, safe_bundle_name))


if __name__ == "__main__":
    bundles, creations, forwards = instance_chains(INSTANCE_PATH)
    dump_graph(
        output_folder=GRAPH_PATH,
        bundles=bundles,
        creations=creations,
        forwards=forwards,
    )
