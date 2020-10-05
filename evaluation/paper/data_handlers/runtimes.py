import json
import glob
import os

from datetime import datetime
from typing import Dict, List, Union, Tuple
from pandas import DataFrame, Timestamp


def log_entry_time(log_entry):
    return datetime.strptime(log_entry["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")


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
    node_path: str, routing_algorithm: str, sim_instance_id: str
) -> Dict[str, List[Dict[str, Union[str, datetime]]]]:
    bundles = {}
    node_id = node_path.split("/")[-1].split(".")[0]
    interesting_event = False
    event = ""
    from_to = None
    metadata_bundles = []

    with open(node_path, "r") as f:
        for line in f.readlines():
            try:
                entry = json.loads(line)
                if entry["msg"] == "REST client sent bundle":  # A bundle is created
                    interesting_event = True
                    event = "creation"
                    from_to = None

                if (
                    entry["msg"] == "Sending bundle to a CLA (ConvergenceSender)"
                ):  # A bundle is about to be sent
                    interesting_event = True
                    event = "sending"
                    from_to = None

                # if (
                #    entry["msg"] == "Sending bundle failed"
                # ):  # A bundle is about to be sent
                #    interesting_event = True
                #    event = "failure"

                if entry["msg"] == "Received bundle from peer":  # Received bundle
                    if entry["bundle"] in metadata_bundles:
                        continue

                    interesting_event = True
                    event = "reception"
                    from_to = entry["src"]["EndpointType"]["Ssp"].replace("/", "")

                if (
                    entry["msg"] == "Received bundle for local delivery"
                ):  # Bundle reached destination
                    interesting_event = True
                    event = "delivery"
                    from_to = None

                if (
                    entry["msg"] == "Selected routing algorithm"
                ):  # Bundle reached destination
                    interesting_event = True
                    event = "start"
                    from_to = None

                if entry["msg"] == "CONTEXT: Is context bundle":
                    metadata_bundles.append(entry["bundle"])

                if interesting_event:
                    events = bundles.get(entry["bundle"], [])
                    events.append(
                        {
                            "routing": routing_algorithm,
                            "sim_instance_id": sim_instance_id,
                            "timestamp": log_entry_time(entry),
                            "event": event,
                            "node": node_id,
                            "from_to": from_to,
                            "bundle": entry["bundle"],
                        }
                    )
                    bundles[entry["bundle"]] = events

                    interesting_event = False
                    event = ""
            except:
                pass

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

    parsed_instances = [parse_bundle_events_instance(path) for path in instance_paths]
    bundle_events: List[Dict[str, Union[str, datetime]]] = []
    for instance in parsed_instances:
        for node in instance:
            for _, events in node.items():
                bundle_events += events
    event_frame = DataFrame(bundle_events)
    event_frame = event_frame.sort_values(by="timestamp")
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
