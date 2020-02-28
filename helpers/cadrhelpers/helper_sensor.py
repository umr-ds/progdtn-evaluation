#! /usr/bin/env python3

import toml
import argparse

from typing import Any, Dict
from random import randint, choice
from dataclasses import dataclass

import cadrhelpers.movement_context as m_c

from cadrhelpers.dtnclient import send_context, build_url
from cadrhelpers.traffic_generator import TrafficGenerator
from cadrhelpers.node_context import SensorContext


def send_integer(url: str, name: str) -> None:
    print(f"Sending random integer context with name '{name}'")
    value = {"value": randint(3, 10)}
    send_context(rest_url=url, context_name=name, node_context=value)


def send_random_context(url: str, context: Dict[str, Any]) -> None:
    """Pick and send a random context-item to the node"""
    name: str = choice(context.keys())
    send_context(rest_url=url, context_name=name, node_context=context[name])


@dataclass()
class ContextGenerator:

    rest_url: str


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate context data & traffic for sensor nodes"
    )
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    config_data = toml.load(args.path)

    with open("/tmp/seed", "rb") as f:
        seed = f.read(4)

    with open("/tmp/routing", "r") as f:
        routing = f.read()

    context = routing == "context"

    context_url = build_url(
        address=config_data["REST"]["address"], port=config_data["REST"]["context_port"]
    )
    bundle_url = build_url(
        address=config_data["REST"]["address"], port=config_data["REST"]["bundle_port"]
    )

    context_helper = ContextGenerator(rest_url=context_url)

    movement_helper: m_c.NS2Movements = m_c.generate_movement(
        rest_url=context_url,
        path=config_data["Scenario"]["movements"],
        node_name=config_data["Node"]["name"],
    )

    nodes: m_c.Nodes = m_c.parse_scenario_xml(path=config_data["Scenario"]["xml"])

    traffic_helper = TrafficGenerator(
        rest_url=bundle_url,
        seed=seed,
        node_name=config_data["Node"]["name"],
        nodes=nodes,
        context=context,
    )

    if context:
        context_generator = SensorContext(
            rest_url=context_url,
            node_name=config_data["Node"]["name"],
            wifi_range=config_data["Scenario"]["wifi_range"],
            nodes=nodes,
        )

    # fork other helpers and daemonise
    movement_helper.run()
    traffic_helper.run()
    if context:
        context_generator.run()
