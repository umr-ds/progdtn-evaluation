import datetime
import json
import glob
import os


def log_entry_time(log_entry):
    return datetime.datetime.strptime(
            log_entry["time"][:-4], "%Y-%m-%dT%H:%M:%S.%f")

def parse_dtnd(dtnd_path):
    bundles = {}
    interesting_event = False
    event = ""
    
    with open(dtnd_path, 'r') as f:
        for line in f.readlines():
            try:
                entry = json.loads(line)
                if entry["msg"] == "Transmission of bundle requested": # A bundle is about to be sent
                    interesting_event = True
                    event = "sending"
                if entry["msg"] == "Incoming bundle": # Received bundle
                    interesting_event = True
                    event = "receiving"
                if entry["msg"] == "Received bundle for local delivery": # Bundle reached destination
                    interesting_event = True
                    event = "local"
                    print(event)
                    
                if interesting_event:
                    events = bundles.get(entry["bundle"], [])
                    events.append({
                        "timestamp": log_entry_time(entry),
                        "event": event
                    })
                    bundles[entry["bundle"]] = events

                    interesting_event = False
                    event = ""
            except:
                pass
    
    return bundles


def parse_bundle_times_instance(instance_path):
    dtnd_paths = glob.glob(os.path.join(instance_path, "*.conf_dtnd_run.log"))
    
    parsed_dtnds = [parse_dtnd(p) for p in dtnd_paths]
    return parsed_dtnds

    
def parse_bundle_times(experiment_path):
    instance_paths = glob.glob(os.path.join(experiment_path, "*"))
    
    parsed_instances = [parse_bundle_times_instance(path) for path in instance_paths]
    
    print(parsed_instances)