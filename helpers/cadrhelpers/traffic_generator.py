import random
import multiprocessing

from hashlib import sha1
from dataclasses import dataclass

from cadrhelpers.movement_context import Nodes


def initialise_rng(seed: bytes, node_name: str) -> None:
    """While we want to initialise each node's RNG deterministically so that experiments can be repeated,
    we can't just initialise it with the seed given by MACI, since then all nodes wold behave the same.

    To solve this, we generate a unique seed for each node by hashing the seed together with the node's name.
    """
    name_binary = bytes(node_name, encoding="utf8")
    unique_seed: bytes = sha1(seed + name_binary).digest()
    random.seed(unique_seed)


@dataclass()
class TrafficGenerator:
    rest_url: str
    seed: bytes
    node_name: str
    nodes: Nodes

    def run(self) -> None:
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self) -> None:
        initialise_rng(seed=self.seed, node_name=self.node_name)
