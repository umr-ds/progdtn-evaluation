import os
import pickle

from typing import Dict, List, Tuple
from dataclasses import dataclass

from preprocessors import node_types


routings = ["context", "epidemic", "prophet", "spray"]


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


def filter_meta_bundles(
    bundles: Dict[str, List[Occurrence]], log_path: str
) -> Dict[str, List[Occurrence]]:
    """As it turns out, if you just parse the logs  you will also get all the metadata bundles.

    While it may be useful to compare the total number of bundles sent, you can't use these to compute delivery times
    and such.
    """
    for _, _, files in os.walk(log_path):
        for file in files:
            if "dtnd_run.log" in file:
                with open(os.path.join(log_path, file), "r") as f:
                    for line in f:
                        if 'bundle="' in line:
                            if "metadata" in line:
                                bundle = get_bundle_id(parts=line.split(" "))
                                occurrences = bundles.get(bundle)
                                if occurrences is not None:
                                    del bundles[bundle]

    return bundles


def compute_bundle_runtimes(
    routing: str, bundles: Dict[str, List[Occurrence]], nodes: Dict[str, str]
):
    print("Computing bundle runtimes")
    # bundle_id and originating node of bundles that were not delivered successfully
    missing_bundles: List[Tuple[str, str]] = []

    with open(f"/research_data/sommer2020cadr/bundle_runtimes_{routing}.csv", "w") as f:
        f.write("routing,bundle,arrived_at,runtime\n")
        for bundle, occurrences in bundles.items():
            print(f"Computing runtime for bundle {bundle}")
            start_time = occurrences[0].timestamp
            arrived = False
            for occurence in occurrences[1:]:
                if nodes[occurence.node] == "backbone":
                    # the first time a bundle is seen on a backbone node, we consider it received
                    print(f"Bundle arrived at node {occurence.node}")
                    receive_time = occurence.timestamp - start_time
                    print(f"Runtime was {receive_time}")
                    f.write(f"{routing},{bundle},{occurence.node},{receive_time}\n")
                    arrived = True
                    break
            if not arrived:
                print("Bundle did not make it to backbone")
                missing_bundles.append((bundle, occurrences[0].node))

    with open(f"/research_data/sommer2020cadr/missing_bundles_{routing}.csv", "w") as f:
        f.write("bundle,origin\n")
        for bundle, origin in missing_bundles:
            f.write(f"{bundle},{origin}\n")


# gets logged when dtnd is about to forward a bundle
start_msg = "Bundle will be forwarded"
# these happen after routing so we will focus on these
stop_msg_after = [
    "Sending bundle to a CLA (ConvergenceSender)",
    "Sending bundle failed",
    "Sending bundle succeeded",
    "Failed to forward bundle to any CLA"
]
# these occur before routing is triggered and should therefore not count
stop_msg_before = [
    "Bundle contains an exceeded hop count block",
    "Bundle's primary block's lifetime is exceeded",
    "Bundle's lifetime is expired",
]


def compute_sender_selection_computetimes(data_path: str, node_types: Dict[str, str], output_path: str):
    print("Computing runtime of sender selection function")
    with open(output_path, "w") as output:
        output.write("routing,node,type,time\n")
        for _, routings, _ in os.walk(data_path):
            for routing in routings:
                print(f"Evaluating {routing}")
                for _, _, files in os.walk(os.path.join(data_path, routing)):
                    for file in files:
                        if "dtnd_run.log" in file:
                            print(f"Parsing {file}")
                            node_name: str = file.split("_")[0]
                            node_type = node_types[node_name]
                            bundles_in_processing: Dict[str, float] = {}
                            with open(os.path.join(data_path, routing, file), "r") as f:
                                for line in f:
                                    if "panic" in line:
                                        break

                                    parts = line.split(" ")
                                    bundle_id = get_bundle_id(parts)
                                    log_time = parts[0].split('"')[1]
                                    timestamp = log_time_to_int(log_time)

                                    if start_msg in line:
                                        bundles_in_processing[bundle_id] = timestamp
                                        continue

                                    for bad_stop in stop_msg_before:
                                        if bad_stop in line:
                                            if bundle_id in bundles_in_processing:
                                                del bundles_in_processing[bundle_id]
                                            continue

                                    for good_stop in stop_msg_after:
                                        if good_stop in line:
                                            if bundle_id in bundles_in_processing:
                                                processing_time = timestamp - bundles_in_processing[bundle_id]
                                                del bundles_in_processing[bundle_id]
                                                output.write(f"{routing},{node_name},{node_type},{processing_time}\n")
                                            continue


if __name__ == "__main__":
    # bundles = parse_simulation_run("/research_data/sommer2020cadr/data/prophet")
    # with open("/research_data/sommer2020cadr/occurrences_prophet.pickle", "wb") as f:
    #     print("Writing data to disk")
    #     pickle.dump(bundles, f)

    print("Loading node types")
    types = node_types(
        scenario_path="/home/msommer/devel/cadr-evaluation/scenarios/wanderwege/wanderwege.xml",
    )

    compute_sender_selection_computetimes(
        data_path="/research_data/sommer2020cadr/data",
        node_types=types,
        output_path="/research_data/sommer2020cadr/selection_compute.csv"
    )

    # for routing in routings:
    #     with open(
    #         f"/research_data/sommer2020cadr/filtered_{routing}.pickle", "rb"
    #     ) as f:
    #         print("Loading bundles occurrences")
    #         bundles = pickle.load(f)
    #        compute_bundle_runtimes(routing=routing, bundles=bundles, nodes=types)

    # with open("/research_data/sommer2020cadr/bundles.csv", "w") as bundles:
    #     bundles.write("routing,bundles\n")
    #     for routing in routings:
    #         with open(
    #             f"/research_data/sommer2020cadr/occurrences_{routing}.pickle", "rb"
    #         ) as f:
    #             b: Dict[str, List[Occurrence]] = pickle.load(f)
    #             filtered = filter_meta_bundles(bundles=b, log_path=f"/research_data/sommer2020cadr/data/{routing}")
    #         with open(f"/research_data/sommer2020cadr/filtered_{routing}.pickle", "wb") as f:
    #             pickle.dump(filtered, f)

    # with open("/research_data/sommer2020cadr/bundles.csv", "w") as bundles:
    #     bundles.write("routing,bundles\n")
    #     for routing in routings:
    #         with open(
    #             f"/research_data/sommer2020cadr/occurrences_{routing}.pickle", "rb"
    #         ) as f:
    #             b: Dict[str, List[Occurrence]] = pickle.load(f)
    #             print(b.keys())
    #             bundles.write(f"{routing},{len(b.keys())}\n")
