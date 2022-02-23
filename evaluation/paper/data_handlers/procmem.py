import glob
import os

import pandas as pd

from .helpers import parse_parameters


PIDSTAT_NUMERICS = [
    "UID",
    "PID",
    "%usr",
    "%system",
    "%guest",
    "%wait",
    "%CPU",
    "CPU",
    "minflt/s",
    "majflt/s",
    "VSZ",
    "RSS",
    "%MEM",
    "StkSize",
    "StkRef",
    "kB_rd/s",
    "kB_wr/s",
    "kB_ccwr/s",
    "iodelay",
]


def parse_pidstat_file(pidstat_path):
    node = os.path.basename(pidstat_path).split(".")[0]
    modify_date = pd.to_datetime(int(os.path.getmtime(pidstat_path)), unit="s").date()

    with open(pidstat_path, "r") as pidstat_file:
        snaps = pidstat_file.read().split("\n\n")
        csv_header = snaps[1].splitlines()[0].split()[1:]
        stats_list = [
            line.split() for snap in snaps[1:] for line in snap.splitlines()[1:]
        ]

        pidstat_df = pd.DataFrame(stats_list, columns=csv_header)

        # prepend log modification date time, convert to datetime
        # pidstat_df["Time"] = str(modify_date) + " " + pidstat_df["Time"]
        pidstat_df["Time"] = pd.to_datetime(pidstat_df["Time"])
        pidstat_df["node"] = node

        pidstat_df[PIDSTAT_NUMERICS] = pidstat_df[PIDSTAT_NUMERICS].apply(pd.to_numeric)

        pidstat_df = pidstat_df.loc[
            ~pidstat_df["Command"].isin(
                [
                    "vnoded",
                    "bwm-ng",
                    "pidstat",
                    "ldconfig",
                    "bash",
                    "sh",
                    "ldconfig.real",
                    "sleep",
                    "tee",
                ]
            )
        ]

        dir_path = os.path.dirname(pidstat_path)
        parameters = parse_parameters(dir_path)

        pidstat_df["routing"] = parameters["routing"]
        pidstat_df["id"] = parameters["simInstanceId"]

        return pidstat_df


def parse_pidstat_instance(instance_path):
    pidstat_paths = glob.glob(os.path.join(instance_path, "*.conf_pidstat"))

    parsed_pidstats = [parse_pidstat_file(path) for path in pidstat_paths]

    pidstat_df = pd.concat(parsed_pidstats)

    pidstat_df = pidstat_df.sort_values(["Time", "node"]).reset_index()
    pidstat_df["dt"] = (
        pidstat_df["Time"] - pidstat_df["Time"].iloc[0]
    ).dt.total_seconds()

    return pidstat_df


def parse_pidstat(binary_files_path):
    experiment_paths = glob.glob(os.path.join(binary_files_path, "*"))

    instance_paths = []
    for experiment_path in experiment_paths:
        instance_paths.extend(glob.glob(os.path.join(experiment_path, "*")))

    parsed_instances = [parse_pidstat_instance(path) for path in instance_paths[:1]]
    df = pd.concat(parsed_instances, sort=False)
    df = df.sort_values(["Time", "id", "node"]).reset_index()

    df = df.groupby(["id", "routing", "dt"]).sum()
    df = df[["%CPU", "RSS"]]

    return df
