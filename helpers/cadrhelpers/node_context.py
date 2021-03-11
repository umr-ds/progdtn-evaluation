#! /usr/bin/env python3

import sys
import argparse
import toml

from cadrhelpers.dtnclient import send_context, build_url
from cadrhelpers.util import compute_euclidean_distance, parse_scenario_xml, Nodes


class GenericContext:
    def __init__(self, rest_url: str, node_type: str):
        print("Initialising GenericContext", flush=True)
        self.rest_url = rest_url
        self.node_type = node_type

    def run(self):
        print("Sending node context.", flush=True)
        send_context(
            rest_url=self.rest_url,
            context_name="role",
            node_context={"node_type": self.node_type},
        )


class SensorContext:
    def __init__(self, rest_url: str, node_name: str, wifi_range: float, nodes: Nodes):
        print("Initialising SensorContext", flush=True)
        self.rest_url: str = rest_url
        self.node_name: str = node_name
        self.wifi_range: float = wifi_range
        self.nodes: Nodes = nodes

    def run(self):
        connectedness = self.compute_connectedness()
        send_context(
            rest_url=self.rest_url,
            context_name="connectedness",
            node_context={"value": str(connectedness)},
        )

    def compute_connectedness(self) -> int:
        """Finds (static) nodes within wifi range"""
        print("Computing connectedness", flush=True)
        connectedness: int = 0

        ourself = self.nodes.get_node_for_name(node_name=self.node_name)

        static_nodes = self.nodes.sensors + self.nodes.backbone

        for node in static_nodes:
            distance = compute_euclidean_distance(node_a=ourself, node_b=node)
            if distance <= self.wifi_range:
                connectedness += 1

        print(f"Connectedness: {connectedness}", flush=True)
        return connectedness


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update the node's context information"
    )
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    node_config = toml.load(args.path)
    print(f"Using config: {node_config}", flush=True)

    if node_config["Experiment"]["routing"] != "context_complex":
        print("Experiment does not require context information", flush=True)
        sys.exit(0)

    nodes: Nodes = parse_scenario_xml(path=node_config["Scenario"]["xml"])
    this_node = nodes.get_node_for_name(node_name=node_config["Node"]["name"])
    print(f"This node's type: {this_node.type}", flush=True)

    routing_url = build_url(
        address=node_config["REST"]["address"], port=node_config["REST"]["routing_port"]
    )

    generic_context = GenericContext(rest_url=routing_url, node_type=this_node.type)
    generic_context.run()

    if this_node.type == "sensor":
        sensor_context = SensorContext(
            rest_url=routing_url,
            node_name=this_node.name,
            wifi_range=node_config["Scenario"]["wifi_range"],
            nodes=nodes,
        )
        sensor_context.run()
