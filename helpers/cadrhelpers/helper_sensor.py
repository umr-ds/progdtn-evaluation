#! /usr/bin/env python3

import toml
import argparse
import time
import daemon
import os
import logging

import cadrhelpers.movement_context as m_c

from cadrhelpers.dtnclient import build_url, get_size
from cadrhelpers.traffic_generator import TrafficGenerator
from cadrhelpers.node_context import SensorContext


def run(rest_url: str, logging_file: str, node_name: str) -> None:
    with open(logging_file, "w", buffering=1) as f:
        while True:
            time.sleep(10)
            now = int(time.time())
            store_size = get_size(rest_url=rest_url)
            logging.debug(f"Store size: {store_size}")
            f.write(f"{now},{node_name},{store_size}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate context data & traffic for sensor nodes"
    )
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    config_data = toml.load(args.path)

    logging.basicConfig(
        level=config_data["Node"]["log_level"], filename=config_data["Node"]["log_file"]
    )

    if os.path.isfile("/tmp/seed"):
        with open("/tmp/seed", "rb") as f:
            seed = f.read(4)
    else:
        seed = b"\x00\x00\x00\x00"
    logging.info(f"Seed: {seed}")

    if os.path.isfile("/tmp/routing"):
        with open("/tmp/routing", "r") as f:
            routing = f.read()
    else:
        routing = "epidemic"
    logging.info(f"Routing Algorithm: {routing}")

    context = routing == "context"
    logging.info(f"Using Context: {context}")

    context_url = build_url(
        address=config_data["REST"]["address"], port=config_data["REST"]["context_port"]
    )
    bundle_url = build_url(
        address=config_data["REST"]["address"], port=config_data["REST"]["bundle_port"]
    )

    nodes: m_c.Nodes = m_c.parse_scenario_xml(path=config_data["Scenario"]["xml"])
    this_node = nodes.get_node_for_name(node_name=config_data["Node"]["name"])

    if this_node.type == "visitor":
        movement_helper: m_c.NS2Movements = m_c.generate_movement(
            rest_url=context_url,
            path=config_data["Scenario"]["movements"],
            node_name=config_data["Node"]["name"],
        )

    if this_node.type == "sensor":
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
    if this_node.type == "sensor":
        traffic_helper.run()
    if context:
        context_generator.run()
    if this_node.type == "visitor":
        movement_helper.run()
    run(
        rest_url=bundle_url,
        logging_file=config_data["Node"]["store_log"],
        node_name=config_data["Node"]["name"],
    )
