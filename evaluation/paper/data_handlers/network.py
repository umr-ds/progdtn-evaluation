import glob
import os
import datetime

import json

from typing import Dict, List, Union, Tuple

import pandas as pd

pd.set_option("display.max_rows", 500)

from .helpers import parse_parameters


BWM_HEADERS_COMPLETE = [
    "ts",
    "iface",
    "bytes_out/s",
    "bytes_in/s",
    "bytes_total/s",
    "bytes_in",
    "bytes_out",
    "packets_out/s",
    "packets_in/s",
    "packets_total/s",
    "packets_in",
    "packets_out",
    "errors_out/s",
    "errors_in/s",
    "errors_in",
    "errors_out",
]

BWM_HEADERS = ["ts", "iface", "bytes_out/s"]

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


def dateparse(time_in_secs):
    return datetime.datetime.fromtimestamp(float(time_in_secs))


def parse_bwm(bwm_path):    
    df = pd.read_csv(bwm_path, sep=";", usecols=[0, 1, 2], names=BWM_HEADERS)

    df["bytes_out/s"] = df["bytes_out/s"].astype(float)

    # BWM tends to spit our very large numbers if not shutdown correctly.
    # We want to avoid them, so just remove large numbers.
    df = df.loc[df["bytes_out/s"] < 54000000 * 100]
    df = df.loc[df["iface"] == "total"]

    df["ts"] = df["ts"].astype(int)
    df["ts"] = pd.to_datetime(df["ts"], unit="s")
    df["node"] = os.path.basename(bwm_path).split(".")[0]

    dir_path = os.path.dirname(bwm_path)
    parameters = parse_parameters(dir_path)

    df["routing"] = parameters["routing"]
    df["id"] = parameters["simInstanceId"]

    return df


def parse_bwms_instance(instance_path):
    param_path = os.path.join(instance_path, "parameters.py")
    params = parse_instance_parameters(path=param_path)
    
    if params["payload_size"] == 10000000: # or params["bundles_per_node"] != 100 or params["routing"] not in ["epidemic", "cadr_epidemic", "cadr_responders"]:
        return pd.DataFrame()
    print(f"Parsing configuarion {params['payload_size']}, {params['bundles_per_node']}, {params['routing']} in {instance_path}")
    
    bwm_paths = glob.glob(os.path.join(instance_path, "*.conf_bwm.csv"))

    parsed_bwms = [parse_bwm(p) for p in bwm_paths]
    df = pd.concat(parsed_bwms)

    df = df.sort_values(["ts", "node"]).reset_index()
    df["dt"] = (df["ts"] - df["ts"].iloc[0]).dt.total_seconds()

    return df


def parse_bwms(binary_files_path):
    experiment_paths = glob.glob(os.path.join(binary_files_path, "*"))

    instance_paths = []
    for experiment_path in experiment_paths:
        instance_paths.extend(glob.glob(os.path.join(experiment_path, "*")))

    parsed_instances = [parse_bwms_instance(path) for path in instance_paths]
    df = pd.concat(parsed_instances, sort=False)
    df = df.sort_values(["ts", "id", "node"]).reset_index()

    df = df.drop(columns=["level_0", "index"])
    df = df.groupby(["id", "routing", "dt"]).sum()
    df["Mbit/s"] = df["bytes_out/s"] / 1024 / 1024 * 8

    return df
