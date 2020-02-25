#! /usr/bin/env python3

import toml
import argparse

from typing import Any, Dict
from random import randint, choice

from cadrhelpers.dtnclient import send_context, build_url
from cadrhelpers.movement_context import NS2Movements, generate_movement
from cadrhelpers.traffic_generator import TrafficGenerator

REST_ADDRESS = "127.0.0.1"
CONTEXT_PORT = 35043
BUNDLE_PORT = 35038
NODE_NAME = "n2"


def send_integer(url: str, name: str) -> None:
    print(f"Sending random integer context with name '{name}'")
    value = {"value": randint(3, 10)}
    send_context(rest_url=url, context_name=name, node_context=value)


def send_random_context(url: str, context: Dict[str, Any]) -> None:
    """Pick and send a random context-item to the node"""
    name: str = choice(context.keys())
    send_context(rest_url=url, context_name=name, node_context=context[name])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate context data & traffic for sensor nodes")
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    config_data = toml.load(args.path)

    with open("/tmp/seed", "rb") as f:
        seed = f.read(4)

    context_url = build_url(address=REST_ADDRESS, port=CONTEXT_PORT)
    bundle_url = build_url(address=REST_ADDRESS, port=BUNDLE_PORT)

    movement_helper: NS2Movements = generate_movement(
        rest_url=context_url,
        path="/dtn_routing/scenarios/randomWaypoint/randomWaypoint.ns_movements",
        node_name=NODE_NAME
    )
    movement_helper.run()

    traffic_helper = TrafficGenerator(
        rest_url=bundle_url,
        seed=seed,
        node_name=NODE_NAME
    )
    traffic_helper.run()
