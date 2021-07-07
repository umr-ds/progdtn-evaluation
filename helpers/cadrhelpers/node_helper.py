#! /usr/bin/env python3

import toml
import argparse
import os
import time

from cadrhelpers.dtnclient import (
    build_url,
    register,
    RESTError,
    fetch_pending,
)
from cadrhelpers.util import Nodes, parse_scenario_xml


def run(rest_url: str, node_type: str) -> None:
    print("Starting store size logging", flush=True)

    if node_type == "coordinator":
        eid = "dtn://coordinator/"
    elif node_type == "civilian":
        eid = "dtn://civilians/"
    else:
        eid = f"dtn://{this_node.name}/"

    try:
        registration_data = register(rest_url=rest_url, endpoint_id=eid)

        while True:
            time.sleep(60)
            # empty store of pending bundles
            new = fetch_pending(rest_url=rest_url, uuid=registration_data["uuid"])
            print(f"Fetched {len(new)} new bundles.", flush=True)

    except RESTError as err:
        print(err, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Will generate metadata and/or traffic depending on node type"
    )
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    config_data = toml.load(args.path)
    print(f"Using config: {config_data}", flush=True)

    agent_url = build_url(
        address=config_data["REST"]["address"], port=config_data["REST"]["agent_port"]
    )

    nodes: Nodes = parse_scenario_xml(path=config_data["Scenario"]["xml"])
    this_node = nodes.get_node_for_name(node_name=config_data["Node"]["name"])
    print(f"This node's type: {this_node.type}", flush=True)

    run(
        rest_url=agent_url,
        node_type=this_node.type,
    )
