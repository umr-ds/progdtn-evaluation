import os

from typing import List

import pandas
from pandas import DataFrame


def load_store_sizes(data_path: str) -> DataFrame:
    """Read in all the data store CSVs and merge them into a single large DataFrame"""
    data: List[DataFrame] = []
    for root, subdirs, _ in os.walk(data_path):
        for directory in subdirs:
            for _, _, files in os.walk(os.path.join(root, directory)):
                for file in files:
                    if "store_log.csv" in file:
                        frame = pandas.read_csv(os.path.join(root, directory, file))
                        data.append(frame)
    return pandas.concat(data)


if __name__ == "__main__":
    data = load_store_sizes("/research_data/sommer2020cadr/data")
    print(data)
