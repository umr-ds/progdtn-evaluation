import random
import multiprocessing
import math
import time
import logging
import string

from dataclasses import dataclass
from hashlib import sha1
from typing import Tuple

import cadrhelpers.dtnclient as dtnclient
from cadrhelpers.movement_context import Nodes, Node
from cadrhelpers.dtnclient import send_context


DESTINATION = "dtn://backbone/"


def compute_euclidean_distance(node_a: Node, node_b: Node) -> float:
    x_diff = math.pow(node_a.x_pos - node_b.x_pos, 2)
    y_diff = math.pow(node_a.y_pos - node_b.y_pos, 2)
    return math.sqrt(x_diff + y_diff)


@dataclass()
class TrafficGenerator:

    agent_url: str
    routing_url: str
    seed: bytes
    node_name: str
    endpoint_id: str
    nodes: Nodes
    context: bool
    context_algorithm: str
    uuid: str = ""
    logger: logging.Logger = logging.getLogger(__name__)

    def run(self) -> None:
        self.logger.info("Starting traffic generator")
        process = multiprocessing.Process(target=self._run)
        process.start()
        self.logger.info("Traffic generator running")

    def _run(self) -> None:
        self.initialise_rng(seed=self.seed, node_name=self.node_name)
        closest_backbone, closest_distance = self.find_closest_backbone()
        self.logger.info(f"Closest backbone: {closest_backbone}")

        self.uuid = dtnclient.register(
            rest_url=self.agent_url, endpoint_id=self.endpoint_id
        )["uuid"]

        if self.context:
            send_context(
                rest_url=self.routing_url,
                context_name="backbone",
                node_context={"distance": str(closest_distance)},
            )

        while True:
            # wait between 1 and 10 minutes and then send a bundle
            sleep_time = random.randint(60, 600)
            self.logger.info(f"Waiting for {sleep_time} seconds")
            time.sleep(sleep_time)

            bundle_type: str = random.choice(["simple", "bulk"])
            self.logger.info(f"Sending {bundle_type} bundle")
            if bundle_type == "simple":
                payload = self.generate_payload(4, 16)
            else:
                # Between 1 and 10 MByte
                payload = self.generate_payload(1000000, 100000000)

            if self.context:
                if self.context_algorithm == "spray":
                    self.send_context_spray(payload=payload)
                else:
                    self.send_context_bundle(
                        payload=payload,
                        bundle_type=bundle_type,
                        closest_backbone=closest_backbone,
                    )
            else:
                self.send_bundle(payload=payload)

    def send_bundle(self, payload: str):
        self.logger.info("Sending bundle without context")
        dtnclient.send_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=DESTINATION,
            source=self.endpoint_id,
            payload=payload,
        )

    def send_context_bundle(
        self, payload: str, bundle_type: str, closest_backbone: Node
    ) -> None:
        self.logger.info("Sending bundle with context")
        timestamp = int(time.time())
        context = {
            "timestamp": str(timestamp),
            "bundle_type": str(bundle_type),
            "x_dest": str(closest_backbone.x_pos),
            "y_dest": str(closest_backbone.y_pos),
        }
        self.logger.info(f"Bundle context: {context}")
        dtnclient.send_context_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=DESTINATION,
            source=self.endpoint_id,
            payload=payload,
            context=context,
        )

    def send_context_spray(self, payload: str) -> None:
        self.logger.info("Sending simulated spray bundle")
        context = {"copies": "5"}
        dtnclient.send_context_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=DESTINATION,
            source=self.endpoint_id,
            payload=payload,
            context=context,
        )

    def find_closest_backbone(self) -> Tuple[Node, float]:
        assert self.nodes.backbone, "There needs to be at least 1 backbone node"

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        closest: Node = self.nodes.backbone[0]
        closest_distance = compute_euclidean_distance(node_a=ourself, node_b=closest)

        for backbone in self.nodes.backbone:
            distance = compute_euclidean_distance(node_a=ourself, node_b=closest)
            if distance < closest_distance:
                closest = backbone
                closest_distance = distance

        return closest, closest_distance

    def initialise_rng(self, seed: bytes, node_name: str) -> None:
        """While we want to initialise each node's RNG deterministically so that experiments can be repeated,
        we can't just initialise it with the seed given by MACI, since then all nodes wold behave the same.

        To solve this, we generate a unique seed for each node by hashing the seed together with the node's name.
        """
        name_binary = bytes(node_name, encoding="utf8")
        node_seed: bytes = sha1(seed + name_binary).digest()
        self.logger.info(f"RNG seed: {node_seed}")
        random.seed(node_seed)

    def generate_payload(self, size_min: int, size_max: int) -> str:
        size: int = random.randint(size_min, size_max)
        payload: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=size)
        )
        return payload
