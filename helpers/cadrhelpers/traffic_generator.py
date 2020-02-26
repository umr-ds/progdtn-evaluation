import random
import multiprocessing
import math
import time
import subprocess

from hashlib import sha1
from dataclasses import dataclass
from base64 import standard_b64encode

import cadrhelpers.dtnclient as dtnclient
from cadrhelpers.movement_context import Nodes, Node


DESTINATION = "dtn:backbone"


def initialise_rng(seed: bytes, node_name: str) -> None:
    """While we want to initialise each node's RNG deterministically so that experiments can be repeated,
    we can't just initialise it with the seed given by MACI, since then all nodes wold behave the same.

    To solve this, we generate a unique seed for each node by hashing the seed together with the node's name.
    """
    name_binary = bytes(node_name, encoding="utf8")
    unique_seed: bytes = sha1(seed + name_binary).digest()
    random.seed(unique_seed)


def generate_payload(size_min: int, size_max: int, in_bytes: bool) -> str:
    size: int = random.randint(size_min, size_max)
    if in_bytes:
        size *= 8
    payload: bytes = random.getrandbits(size)
    return standard_b64encode(payload)


def send_bundle(payload: str):
    subprocess.call(f'dtncat send "http://127.0.0.1:8080" <<< {payload}', shell=True)


@dataclass()
class TrafficGenerator:
    rest_url: str
    seed: bytes
    node_name: str
    x_pos: float
    y_pos: float
    nodes: Nodes
    context: bool

    def run(self) -> None:
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self) -> None:
        initialise_rng(seed=self.seed, node_name=self.node_name)
        closest_backbone = self._find_closest_backbone()

        while True:
            # wait 1 and 10 minutes and then send a bundle
            sleep_time = random.randint(60, 600)
            time.sleep(sleep_time)

            bundle_type = random.choice(("simple", "bulk"))
            if bundle_type == "simple":
                payload = generate_payload(32, 128, False)
            else:
                # Between 1 and 10 MByte
                payload = generate_payload(1000000, 100000000, True)

            if self.context:
                self._send_context_bundle(
                    payload=payload,
                    bundle_type=bundle_type,
                    closest_backbone=closest_backbone,
                )
            else:
                send_bundle(payload=payload)

    def _send_context_bundle(
        self, payload: str, bundle_type: str, closest_backbone: Node
    ):
        timestamp = int(time.time())
        context = {
            "timestamp": timestamp,
            "bundle_type": bundle_type,
            "destination": {"x": closest_backbone.x_pos, "y": closest_backbone.y_pos},
        }
        dtnclient.send_bundle(
            rest_url=self.rest_url,
            bundle_recipient=DESTINATION,
            bundle_payload=payload,
            bundle_context=context,
        )

    def _find_closest_backbone(self) -> Node:
        assert self.nodes.backbone, "There needs to be at least 1 backbone node"
        closest: Node = self.nodes.backbone[0]
        closest_distance = self._compute_euclidean_distance(other=closest)

        for backbone in self.nodes.backbone:
            distance = self._compute_euclidean_distance(other=backbone)
            if distance < closest_distance:
                closest = backbone
                closest_distance = distance

        return closest

    def _compute_euclidean_distance(self, other: Node) -> float:
        x_diff = math.pow(self.x_pos - other.x_pos, 2)
        y_diff = math.pow(self.y_pos - other.y_pos, 2)
        return math.sqrt(x_diff + y_diff)
