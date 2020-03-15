import os
import pickle

from typing import Dict, List
from dataclasses import dataclass


@dataclass()
class Occurrence:
    bundle: str
    node: str
    timestamp: int


def log_time_to_int(time_string: str) -> int:
    timestamp: int = 0
    split = time_string.split(":")
    # hours in milliseconds
    timestamp += int(split[0]) * 3600000
    # minutes in milliseconds
    timestamp += int(split[1]) * 60000
    seconds = split[2].split(".")
    timestamp += int(seconds[0]) * 1000
    timestamp += int(seconds[1])
    return timestamp


def get_bundle_id(parts: List[str]) -> str:
    for part in parts:
        if 'bundle="' in part:
            return part.split('"')[1]


def parse_simulation_run(path: str) -> Dict[str, List[Occurrence]]:
    """Parse the log files of a single simulation run"""
    bundles: Dict[str, List[Occurrence]] = {}
    for _, _, files in os.walk(path):
        for file in files:
            if "dtnd_run.log" in file:
                node_name: str = file.split("_")[0]
                print(f"Parsing {file}")
                with open(os.path.join(path, file), "r") as f:
                    for line in f:
                        if 'bundle="' in line:
                            # something to do with a bundle
                            parts = line.split(" ")
                            log_time = parts[0].split('"')[1]
                            timestamp = log_time_to_int(time_string=log_time)
                            bundle = get_bundle_id(parts=parts)
                            occurrence = Occurrence(
                                bundle=bundle, node=node_name, timestamp=timestamp
                            )
                            bundle_occurrences = bundles.get(bundle)
                            if bundle_occurrences is None:
                                bundles[bundle] = [occurrence]
                            else:
                                bundle_occurrences.append(occurrence)

    print("Soring occurrences for timestamps")
    for bundle, occurrences in bundles.items():
        bundles[bundle] = sorted(
            occurrences, key=lambda occurrence: occurrence.timestamp
        )

    return bundles


if __name__ == "__main__":
    bundles = parse_simulation_run("/research_data/sommer2020cadr/data/prophet")
    with open("/research_data/sommer2020cadr/occurrences_prophet.pickle", "wb") as f:
        print("Writing data to disk")
        pickle.dump(bundles, f)
