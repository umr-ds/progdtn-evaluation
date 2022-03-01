import json
import glob
import os
import numpy as np

from datetime import datetime
from typing import Dict, List, Union, Tuple
from pandas import DataFrame, Timestamp

from data_handlers.preprocessors import node_types


def log_entry_time(log_entry):
    return datetime.strptime(log_entry["time"][:26], "%Y-%m-%dT%H:%M:%S.%f")


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


def parse_node(
    node_path: str, routing_algorithm: str, sim_instance_id: str, payload_size: int, bundles_per_node: int
) -> Dict[str, List[Dict[str, Union[str, int, datetime]]]]:
    
    print(f"Parsing node path {node_path}")
    
    bundles = {}
    node_id = node_path.split("/")[-1].split(".")[0]
    interesting_event = False
    event = ""
    from_to = None
    metadata_bundles = {}
    already_received = []
    bundle_for_civilian = "dtn://civilians/"
    routing_start_time = 0
    routing_end_time = 0
    
    routing_runtimes = {}

    with open(node_path, "r") as f:
        for line in f.readlines():
            try:
                routing_time = 0
                entry = json.loads(line)
                bundle_size = np.nan
                
                if entry["msg"] == "Starting routing decision": # The routing decision started
                    interesting_event = True
                    routing_start_time = log_entry_time(entry)
                    routing_runtimes[entry['bundle']] = routing_start_time
                    event = "routing_start"
                    
                if entry["msg"] == "Routing decision finished": # The routing decision finished
                    interesting_event = True
                    routing_end_time = log_entry_time(entry)
                    tmp_routing_start = routing_runtimes[entry['bundle']]
                    routing_time = routing_end_time - tmp_routing_start
                    del routing_runtimes[entry['bundle']]
                    event = "routing_end"
                
                if entry["msg"] == "REST client sent bundle":  # A bundle is created
                    bundle_size = entry["size"]
                    interesting_event = True
                    event = "creation"

                elif entry["msg"] == "Sending bundle to a CLA (ConvergenceSender)": # A bundle is about to be sent
                    interesting_event = True
                    event = "sending"
                
                elif entry["msg"] == "Received bundle from peer":  # Received bundle               
                    interesting_event = True
                    event = "reception"
                    
                    if bundle_for_civilian == entry["dst"]:
                        if entry['bundle'] not in already_received:
                            already_received.append(entry['bundle'])
                            event = "delivery"

                elif entry["msg"] == "Received bundle for local delivery":  # Bundle reached destination
                    interesting_event = True
                    event = "delivery"

                elif entry["msg"] == "Selected routing algorithm":
                    interesting_event = True
                    event = "start"
                    
                elif entry["msg"] == "CADR: Is context bundle": # Meta data bundle for context algorithms
                    meta_bundle_id = entry["bundle"]
                    meta_bundle_size = entry["Metadata Size"]
                    metadata_bundles[meta_bundle_id] = meta_bundle_size
                    
                elif entry["msg"] == "Received metadata": # Meta data bundle for DTLSR and Prophet
                    meta_bundle_id = entry["bundle"]
                    meta_bundle_size = entry["Metadata Size"]
                    metadata_bundles[meta_bundle_id] = meta_bundle_size

                if interesting_event:
                    events = bundles.get(entry["bundle"], [])
                    events.append(
                        {
                            "routing": routing_algorithm,
                            "sim_instance_id": sim_instance_id,
                            "payload_size": payload_size,
                            "bundles_per_node": bundles_per_node,
                            "timestamp": log_entry_time(entry),
                            "event": event,
                            "node": node_id,
                            "bundle": entry["bundle"],
                            "bundle_size": bundle_size,
                            "routing_time": routing_time,
                        }
                    )
                    bundles[entry["bundle"]] = events

                    interesting_event = False
                    event = ""    
            except:
                pass
            
    for bundle_id in bundles:
        bundle_list = bundles[bundle_id]
        for bundle_entry in bundle_list:
            bundle_entry_id = bundle_entry["bundle"]
            if bundle_entry_id in metadata_bundles:
                is_meta = True
                meta_size = metadata_bundles[bundle_entry_id]
            else:
                is_meta = False
                meta_size = 0
            
            bundle_entry['meta'] = is_meta
            bundle_entry["meta_bundle_size"] = meta_size

    return bundles


def parse_bundle_events_instance(
    instance_path: str,
) -> List[Dict[str, List[Dict[str, Union[str, datetime]]]]]:
    print(f"Parsing {instance_path}")
    node_paths = glob.glob(os.path.join(instance_path, "*.conf_dtnd_run.log"))
    param_path = os.path.join(instance_path, "parameters.py")
    params = parse_instance_parameters(path=param_path)

    parsed_nodes = [
        parse_node(
            node_path=p,
            routing_algorithm=params["routing"],
            payload_size=params["payload_size"],
            bundles_per_node=params["bundles_per_node"],
            sim_instance_id=params["simInstanceId"],
        )
        for p in node_paths
    ]
    return parsed_nodes


def parse_bundle_events(experiment_path: str) -> DataFrame:
    experiment_paths = glob.glob(os.path.join(experiment_path, "*"))

    instance_paths = []
    for experiment_path in experiment_paths:
        instance_paths.extend(glob.glob(os.path.join(experiment_path, "*")))

    parsed_instances = [parse_bundle_events_instance(path) for path in instance_paths if "633" in path]
    bundle_events: List[Dict[str, Union[str, datetime]]] = []
    for instance in parsed_instances:
        for node in instance:
            for _, events in node.items():
                bundle_events += events
    event_frame = DataFrame(bundle_events)
    event_frame = event_frame.sort_values(by="timestamp")
    
    print("Setting node types")
    types = node_types(scenario_path="/storage/research_data/sommer2020cadr/maci-docker-compose/maci_data/scenarios/responders/responders.xml")
    type_frame = DataFrame(types.items(), columns=["node", "node_type"])
    
    merged_df = event_frame.merge(type_frame, how="left", on="node")
    
    print("Filling NaN bundle sizes")
    event_frame = merged_df
    event_frame["bundle_size"] = event_frame.groupby("bundle")["bundle_size"].transform(lambda x: x.fillna(x.mean()))
    
    print("Setting meta data sizes")
    # TODO: parse, not guess.
    event_frame['bundle_size'] = event_frame['bundle_size'].mask(event_frame['bundle_size'].isna(), np.random.uniform(100, 1000, size=len(event_frame)))
    
    print("Computing time delta")
    time_df = DataFrame()
    for _, instance in event_frame.groupby("sim_instance_id"):
        instance_start = instance["timestamp"].iloc[0]
        instance["timestamp_relative"] = instance["timestamp"] - instance_start
        time_df = time_df.append(instance)

    event_frame = time_df
    
    print("Parsing done")
    return event_frame


def compute_bundle_runtimes(
    event_frame: DataFrame,
) -> Tuple[List[str], List[str], List[str], DataFrame]:
    bundles: List[str] = event_frame.bundle.unique().tolist()
    bundle_runtimes: List[Dict[str, Union[str, int]]] = []
    successful: List[str] = []
    unsuccessful: List[str] = []

    for bundle in bundles:
        bundle_events = event_frame[event_frame.bundle == bundle]
        creation = bundle_events[bundle_events.event == "creation"]
        if creation.empty:
            print(f"Bundle {bundle} was not created?")
            continue

        creation_time: Timestamp = creation["timestamp"].iloc[0]

        delivery = bundle_events[bundle_events.event == "delivery"]
        delivered = not delivery.empty

        if delivered:
            successful.append(bundle)
            delivery_time: Timestamp = delivery["timestamp"].iloc[0]
            bundle_runtimes.append(
                {
                    "routing": bundle_events["routing"].iloc[0],
                    "bundle": bundle,
                    "duration_s": (delivery_time - creation_time).seconds,
                }
            )
        else:
            unsuccessful.append(bundle)

        runtimes_df = DataFrame(bundle_runtimes)

    return bundles, successful, unsuccessful, runtimes_df


if __name__ == "__main__":
    event_frame = parse_bundle_events("/research_data/epidemic")
    # _, _, _, times = compute_bundle_runtimes(event_frame=event_frame)
    event_frame.to_csv("/research_data/cadr.csv")
