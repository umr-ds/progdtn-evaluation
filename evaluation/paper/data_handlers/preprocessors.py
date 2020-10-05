import os

from typing import List, Dict

import pandas as pd
from pandas import DataFrame

from cadrhelpers.movement_context import parse_scenario_xml


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
    """Read in all the data store CSVs and merge them into a single large DataFrame

    Also filter out data from crashed nodes
    """
    data: List[DataFrame] = []
    for root, subdirs, _ in os.walk(data_path):
        for directory in subdirs:
            print(f"Loading {directory}")
            simulation_directory = os.path.join(root, directory)
            for _, _, files in os.walk(simulation_directory):
                for file in files:
                    if "store_log.csv" in file:
                        node_name: str = file.split("_")[0]
                        # node_crashed = check_node_crash(
                        #     simulation_directory=simulation_directory,
                        #     node_name=node_name,
                        # )
                        # if not node_crashed:
                        frame = pd.read_csv(os.path.join(root, directory, file))
                        data.append(frame)
    return pd.concat(data)


def final_value(data: DataFrame) -> DataFrame:
    """Extracts the final measurement for each node"""
    filtered: List[DataFrame] = []
    for node in data["node"].unique():
        node_data = data.loc[data["node"] == node]
        sorted_data = node_data.sort_values(by=["timestamp"])
        final_measurement = sorted_data.tail(1)
        filtered.append(final_measurement)
    return pd.concat(filtered)


def node_types(scenario_path: str) -> Dict[str, str]:
    """Reads node definitions from scenario_path and writes a csv of the node<->type mapping to data path"""
    types: Dict[str, str] = {}
    nodes = parse_scenario_xml(path=scenario_path)
    all_nodes = nodes.backbone + nodes.sensors + nodes.visitors
    for node in all_nodes:
        # print(f"Node {node.name} is a {node.type}")
        types[node.name] = node.type
    return types


def add_node_type(data: DataFrame, node_types: Dict[str, str]) -> DataFrame:
    type_column: List[str] = []
    for node in data["node"]:
        type_column.append(node_types[node])
    data["node_type"] = type_column
    return data


if __name__ == "__main__":
    data = load_store_sizes("/research_data/sommer2020cadr/data")
    types = node_types(
        scenario_path="/home/msommer/devel/cadr-evaluation/scenarios/wanderwege/wanderwege.xml",
    )
    data_with_types = add_node_type(data=data, node_types=types)
    data_with_types.to_csv("/research_data/sommer2020cadr/combined.csv")
