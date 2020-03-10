#! /usr/bin/env python3

import os
import shutil

DATA_DIRECTORY = "/research_data/data"


def save_instance_logs(save_path: str, core_directory: str) -> None:
    print(f"Copying data in directory: {core_directory}")
    print(f"Copying to directory: {save_path}")
    for _, node_directories, _ in os.walk(core_directory):
        for node_directory in node_directories:
            node_name = node_directory.split(".")[0]
            for _, _, files in os.walk(os.path.join(core_directory, node_directory)):
                for file in files:
                    if ".log" in file or ".csv" in file:
                        filename = f"{node_name}_{file}"
                        file_src = os.path.join(core_directory, node_directory, file)
                        file_dst = os.path.join(save_path, filename)
                        print(f"Copy {file_src} to {file_dst}")
                        shutil.copyfile(src=file_src, dst=file_dst)


if __name__ == "__main__":
    if os.path.isfile("/tmp/routing"):
        with open("/tmp/routing", "r") as f:
            routing = f.read().strip()
    else:
        routing = "epidemic"
    print(f"Routing Algorithm: {routing}")

    copy_path = os.path.join(DATA_DIRECTORY, routing)
    print(f"Copying data to {copy_path}")
    os.mkdir(copy_path)

    for root, subdirs, _ in os.walk("/tmp"):
        for directory in subdirs:
            if "pycore" in directory:
                save_instance_logs(
                    save_path=copy_path, core_directory=os.path.join(root, directory)
                )
