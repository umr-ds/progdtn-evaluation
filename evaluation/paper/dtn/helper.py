from .forban import Forban
from .dtn7 import DTN7
from .ibr_dtn import IBRDTN
from .serval import Serval

from data_handlers.helpers import parse_parameters


def parse_experiment(experiment_dir):
    "Parses a MACI experiment and returns the correct sub class of DtnSoftware"
    parameters_data = parse_parameters(experiment_dir)
    
    return {
            "DTN7": DTN7,
            "IBRDTN": IBRDTN,
            "Serval": Serval,
            "Forban": Forban,
            }[parameters_data["software"]](experiment_dir)
