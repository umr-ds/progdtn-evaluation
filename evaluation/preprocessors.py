import os

from typing import List

import pandas
from pandas import DataFrame

from cadrhelpers.movement_context import Nodes, parse_scenario_xml


def check_node_crash(simulation_directory: str, node_name: str) -> bool:
    """Check the node's dtnd_run.log to see if dtnd crashed during the simulation.

    In the version of dtnd against which this project has been built, there exists a race condition which can
    crash the routing daemon on node disconnection
    """
    file_name = f"{node_name}_dtnd_run.log"
    with open(os.path.join(simulation_directory, file_name), "r") as f:
        for line in f:
            if "panic" in line:
                print(f"Node {node_name} crashed")
                return True

    return False


def load_store_sizes(data_path: str) -> DataFrame:
    """Read in all the data store CSVs and merge them into a single large DataFrame"""
    data: List[DataFrame] = []
    for root, subdirs, _ in os.walk(data_path):
        for directory in subdirs:
            print(f"Loading {directory}")
            simulation_directory = os.path.join(root, directory)
            for _, _, files in os.walk(simulation_directory):
                for file in files:
                    if "store_log.csv" in file:
                        node_name: str = file.split("_")[0]
                        node_crashed = check_node_crash(
                            simulation_directory=simulation_directory,
                            node_name=node_name,
                        )
                        if not node_crashed:
                            frame = pandas.read_csv(os.path.join(root, directory, file))
                            data.append(frame)
    return pandas.concat(data)


def node_types(scenario_path: str, data_path: str) -> None:
    """Reads node definitions from scenario_path and writes a csv of the node<->type mapping to data path"""
    nodes = parse_scenario_xml(path=scenario_path)
    with open(data_path, "w") as f:
        all_nodes = nodes.backbone + nodes.sensors + nodes.visitors
        f.write("node,type\n")
        for node in all_nodes:
            print(f"Node {node.name} is {node.type}")
            f.write(f"{node.name},{node.type}\n")


if __name__ == "__main__":
    # data = load_store_sizes("/research_data/sommer2020cadr/data")
    # data.to_csv("/research_data/sommer2020cadr/combined.csv")
    node_types(
        scenario_path="/home/msommer/devel/cadr-evaluation/scenarios/wanderwege/wanderwege.xml",
        data_path="/research_data/sommer2020cadr/node_types.csv"
    )
