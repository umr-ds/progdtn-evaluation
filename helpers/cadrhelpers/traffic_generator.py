#! /usr/bin/env python3

import random
import time
import string
import argparse
import sys
import toml

from dataclasses import dataclass
from hashlib import sha1
from typing import Tuple, List
from requests.exceptions import Timeout

import cadrhelpers.dtnclient as dtnclient
from cadrhelpers.dtnclient import send_context, build_url
from cadrhelpers.util import (
    is_context,
    compute_euclidean_distance,
    parse_scenario_xml,
    Node,
    Nodes,
)

T_START = 30
T_STOP = 600


def compute_wait_times(t_start: int, t_stop: int, count: int) -> List[int]:
    send_times: List[int] = []
    runtime = t_stop - t_start
    slot_length = int(runtime / count)

    slot_start = t_start
    slot_stop = t_start + slot_length
    while len(send_times) < count:
        send_time = random.randint(slot_start, slot_stop)
        send_times.append(send_time)
        slot_start = slot_stop + 1
        slot_stop = slot_start + slot_length

    print(f"{time.time()}: Timestamps for bundle generation: {send_times}", flush=True)

    wait_times: List[int] = [send_times[0]]
    timestamp: int = send_times[0]
    for send_time in send_times[1:]:
        wait_times.append(send_time - timestamp)
        timestamp = send_time

    print(f"{time.time()}: Wait times for these timestamps: {wait_times}", flush=True)

    return wait_times


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
    payload_size: int
    number_of_bundles: int
    destination: str
    generate_payload: bool = True
    payload: str = ""
    payload_path: str = ""
    uuid: str = ""

    def run(self) -> None:
        print(f"{time.time()}: Using context {self.context}", flush=True)
        if self.context:
            print(f"{time.time()}: Context algorithm: {self.context_algorithm}", flush=True)

        self.initialise_rng(seed=self.seed, node_name=self.node_name)
        # closest_backbone, closest_distance = self.find_closest_backbone()
        # print(f"{time.time()}: Closest backbone: {closest_backbone}", flush=True)

        wait_times = compute_wait_times(T_START, T_STOP, self.number_of_bundles)

        self.uuid = dtnclient.register(
            rest_url=self.agent_url, endpoint_id=self.endpoint_id
        )["uuid"]

        if self.context_algorithm == "complex":
            send_context(
                rest_url=self.routing_url,
                context_name="backbone",
                node_context={"distance": closest_distance},
            )

        if not self.generate_payload:
            self._load_payload()

        for sleep_time in wait_times:
            try:
                print(f"{time.time()}: Waiting for {sleep_time} seconds", flush=True)
                time.sleep(sleep_time)

                if self.generate_payload:
                    self.payload = self._generate_payload()

                if self.context:
                    if self.context_algorithm == "spray":
                        self.send_context_spray(payload=self.payload)
                    elif self.context_algorithm == "complex":
                        self.send_context_bundle(
                            payload=self.payload,
                            closest_backbone=closest_backbone,
                        )
                    else:
                        self.send_with_empty_context(payload=self.payload)
                else:
                    self.send_bundle(payload=self.payload)
            except Timeout:
                print(f"{time.time()}: Sending caused timeout", flush=True)

        print(f"{time.time()}: Done sending", flush=True)

    def send_bundle(self, payload: str):
        print(f"{time.time()}: Sending bundle without context", flush=True)
        dtnclient.send_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=self.destination,
            source=self.endpoint_id,
            payload=payload,
        )
        print(f"{time.time()}: Bundle sent", flush=True)

    def send_context_bundle(self, payload: str, closest_backbone: Node) -> None:
        print(f"{time.time()}: Sending bundle with context", flush=True)
        timestamp = int(time.time())
        context = {
            "timestamp": str(timestamp),
            "x_dest": str(closest_backbone.x_pos),
            "y_dest": str(closest_backbone.y_pos),
        }
        print(f"{time.time()}: Bundle context: {context}", flush=True)
        dtnclient.send_context_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=self.destination,
            source=self.endpoint_id,
            payload=payload,
            context=context,
        )
        print(f"{time.time()}: Bundle sent", flush=True)

    def send_context_spray(self, payload: str) -> None:
        print(f"{time.time()}: Sending simulated spray bundle", flush=True)
        context = {"copies": "5"}
        dtnclient.send_context_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=self.destination,
            source=self.endpoint_id,
            payload=payload,
            context=context,
        )

    def send_with_empty_context(self, payload: str) -> None:
        print(f"{time.time()}: Sending conext bundle with empty context", flush=True)
        context = {}
        dtnclient.send_context_bundle(
            rest_url=self.agent_url,
            uuid=self.uuid,
            destination=self.destination,
            source=self.endpoint_id,
            payload=payload,
            context=context,
        )
        print(f"{time.time()}: Bundle sent", flush=True)

    def find_closest_backbone(self) -> Tuple[Node, float]:
        assert self.nodes.backbone, "There needs to be at least 1 backbone node"

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        closest: Node = self.nodes.backbone[0]
        closest_distance = compute_euclidean_distance(node_a=ourself, node_b=closest)

        for backbone in self.nodes.backbone:
            distance = compute_euclidean_distance(node_a=ourself, node_b=backbone)
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
        print(f"{time.time()}: RNG seed: {node_seed}", flush=True)
        random.seed(node_seed)

    def _load_payload(self) -> None:
        print(f'{time.time()}: Loading payload')
        with open(self.payload_path, "r") as f:
            self.payload = f.read()
        print(f'{time.time()}: Payload size: {len(self.payload)}')

    def _generate_payload(self) -> str:
        print(f'{time.time()}: Generating payload')
        payload: str = "".join(
            random.choices(string.ascii_letters + string.digits, k=self.payload_size)
        )
        return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generates simulation traffic.")
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    node_config = toml.load(args.path)
    print(f"{time.time()}: Using config: {node_config}", flush=True)

    nodes: Nodes = parse_scenario_xml(path=node_config["Scenario"]["xml"])
    this_node = nodes.get_node_for_name(node_name=node_config["Node"]["name"])
    print(f"{time.time()}: This node's type: {this_node.type}", flush=True)

    destination = ""
    if this_node.type == "civilian":
        destination = "dtn://coordinator/"
    elif this_node.type == "coordinator":
        destination = "dtn://civilians/"
    else:
        print(f"{time.time()}: Node type does not produce bundles.", flush=True)
        sys.exit(0)

    routing_url = build_url(
        address=node_config["REST"]["address"], port=node_config["REST"]["routing_port"]
    )
    agent_url = build_url(
        address=node_config["REST"]["address"], port=node_config["REST"]["agent_port"]
    )

    seed = bytes([node_config["Experiment"]["seed"]])
    context, context_algorithm = is_context(node_config["Experiment"]["routing"])

    traffig_generator = TrafficGenerator(
        destination=destination,
        agent_url=agent_url,
        routing_url=routing_url,
        seed=seed,
        node_name=this_node.name,
        endpoint_id=node_config["Node"]["endpoint_id"],
        nodes=nodes,
        context=context,
        context_algorithm=context_algorithm,
        payload_size=node_config["Experiment"]["payload_size"],
        generate_payload=node_config["Experiment"]["generate_payload"],
        payload_path=node_config["Experiment"]["payload_path"],
        number_of_bundles=node_config["Experiment"]["bundles_per_node"],
    )
    traffig_generator.run()
    print(f"{time.time()}: Terminated", flush=True)
