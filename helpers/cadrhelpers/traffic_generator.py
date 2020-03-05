import random
import multiprocessing
import math
import time
import subprocess
import logging

from hashlib import sha1
from dataclasses import dataclass
from base64 import standard_b64encode

import cadrhelpers.dtnclient as dtnclient
from cadrhelpers.movement_context import Nodes, Node


DESTINATION = "dtn:backbone"


def compute_euclidean_distance(node_a: Node, node_b: Node) -> float:
    x_diff = math.pow(node_a.x_pos - node_b.x_pos, 2)
    y_diff = math.pow(node_a.y_pos - node_b.y_pos, 2)
    return math.sqrt(x_diff + y_diff)


@dataclass()
class TrafficGenerator:
    rest_url: str
    seed: bytes
    node_name: str
    nodes: Nodes
    context: bool
    logger: logging.Logger = logging.getLogger(__name__)

    def run(self) -> None:
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self) -> None:
        self.initialise_rng(seed=self.seed, node_name=self.node_name)
        closest_backbone = self.find_closest_backbone()
        self.logger.debug(f"Closest backbone: {closest_backbone}")

        while True:
            # wait between 1 and 10 minutes and then send a bundle
            sleep_time = random.randint(60, 600)
            self.logger.debug(f"Waiting for {sleep_time} seconds")
            time.sleep(sleep_time)

            bundle_type = random.choice(["simple"])
            self.logger.debug(f"Sending {bundle_type} bundle")
            if bundle_type == "simple":
                payload = self.generate_payload(32, 128, False)
            else:
                # Between 1 and 10 MByte
                # FIXME: Process dies when trying large payloads
                payload = self.generate_payload(1000000, 100000000, True)

            if self.context:
                self.send_context_bundle(
                    payload=payload,
                    bundle_type=bundle_type,
                    closest_backbone=closest_backbone,
                )
            else:
                self.send_bundle(payload=payload)

    def send_context_bundle(
        self, payload: str, bundle_type: str, closest_backbone: Node
    ):
        self.logger.debug("Sending bundle with context")
        timestamp = int(time.time())
        context = {
            "timestamp": timestamp,
            "bundle_type": bundle_type,
            "destination": {"x": closest_backbone.x_pos, "y": closest_backbone.y_pos},
        }
        self.logger.debug(f"Bundle context: {context}")
        dtnclient.send_bundle(
            rest_url=self.rest_url,
            bundle_recipient=DESTINATION,
            bundle_payload=payload,
            bundle_context=context,
        )

    def find_closest_backbone(self) -> Node:
        assert self.nodes.backbone, "There needs to be at least 1 backbone node"

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        closest: Node = self.nodes.backbone[0]
        closest_distance = compute_euclidean_distance(node_a=ourself, node_b=closest)

        for backbone in self.nodes.backbone:
            distance = compute_euclidean_distance(node_a=ourself, node_b=closest)
            if distance < closest_distance:
                closest = backbone
                closest_distance = distance

        return closest

    def initialise_rng(self, seed: bytes, node_name: str) -> None:
        """While we want to initialise each node's RNG deterministically so that experiments can be repeated,
        we can't just initialise it with the seed given by MACI, since then all nodes wold behave the same.

        To solve this, we generate a unique seed for each node by hashing the seed together with the node's name.
        """
        name_binary = bytes(node_name, encoding="utf8")
        unique_seed: bytes = sha1(seed + name_binary).digest()
        self.logger.debug(f"RNG seed: {unique_seed}")
        random.seed(unique_seed)

    def generate_payload(self, size_min: int, size_max: int, in_bytes: bool) -> str:
        size: int = random.randint(size_min, size_max)
        if in_bytes:
            size *= 8
        self.logger.debug(f"Generating payload of size {size}")
        payload: bytes = random.getrandbits(size).to_bytes(
            (int(size / 8)) + 1, byteorder="little", signed=False
        )
        return str(standard_b64encode(payload), "utf-8")

    def send_bundle(self, payload: str):
        self.logger.debug("Sending bundle without context")
        command = f'dtncat send "http://127.0.0.1:8080" "{DESTINATION}" <<< {payload}'
        subprocess.call(command, shell=True)
