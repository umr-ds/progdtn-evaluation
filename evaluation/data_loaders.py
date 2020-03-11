import os

from typing import List

import pandas
from pandas import DataFrame


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


if __name__ == "__main__":
    data = load_store_sizes("/research_data/sommer2020cadr/data")
    print(data)
