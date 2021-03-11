#! /usr/bin/env python3

import argparse
import multiprocessing
import time
import math
import toml
import sys

from typing import List, Tuple, Dict

from cadrhelpers.dtnclient import send_context, build_url
from cadrhelpers.util import parse_scenario_xml, Nodes


class NS2Movement:
    """Single movement command"""

    def __init__(self, timestamp: int, x_dest: float, y_dest: float, speed: float):
        self.timestamp: int = timestamp
        self.x_dest: float = x_dest
        self.y_dest: float = y_dest
        self.speed: float = speed


class NS2Movements:
    """A node's movements as specified in a ns2 movement script

    Attributes:
        node_name: Self explanatory
        rest_url: URL of the context-REST-interface
        step: Current position in the list of movements
        x_pos: X coordinate of current position
        y_pos: Y coordinate of current position
        movements: List of movement commands in the form (timestamp, dest_x_pos, dest_y_pos, speed)
    """

    def __init__(
        self,
        node_name: str,
        rest_url: str,
        x_pos: float,
        y_pos: float,
        movements: List[NS2Movement],
    ):
        self.node_name: str = node_name
        self.rest_url: str = rest_url
        self.x_pos: float = x_pos
        self.y_pos: float = y_pos
        self.movements: List[NS2Movement] = movements
        self.step: int = 0

    def run(self) -> None:
        print("Starting movement context updater.", flush=True)

        # differentiate between node who start moving immediately and those who take a while to get going
        if self.movements[0].timestamp != 0:
            print(
                f"No inital movement, waiting for {self.movements[0].timestamp} seconds",
                flush=True,
            )
            time.sleep(self.movements[0].timestamp)

        vector = self.compute_vector()
        print(f"New movement vector: {vector}", flush=True)
        self.update_context(vector)
        self.move_step()
        print(f"Position at end of movement: ({self.x_pos}, {self.y_pos})", flush=True)

        # main wait-and-update-loop
        while self.step < len(self.movements):
            wait_time: int = (
                self.movements[self.step].timestamp
                - self.movements[self.step - 1].timestamp
            )
            print(f"Next change in movement in {wait_time} seconds", flush=True)
            time.sleep(wait_time)
            vector = self.compute_vector()
            print(f"New movement vector: {vector}", flush=True)
            self.update_context(vector)
            self.move_step()
            print(
                f"Position at end of movement: ({self.x_pos}, {self.y_pos})", flush=True
            )

    def move_step(self) -> None:
        """Update the node's internal position and step counter"""
        self.x_pos = self.movements[self.step].x_dest
        self.y_pos = self.movements[self.step].y_dest
        self.step += 1

    def update_context(self, vector: Tuple[float, float]) -> None:
        """Update node context in dtnd"""
        context: Dict[str, float] = {"x": vector[0], "y": vector[1]}
        print(f"Sending movement vector to dtnd: {context}", flush=True)
        send_context(
            rest_url=self.rest_url, context_name="movement", node_context=context
        )

    def compute_vector(self) -> Tuple[float, float]:
        """Take the node's current position and destination/speed and compute the movement vector"""
        # subtract current position vector from position vector of destination to get direction
        x_move = self.movements[self.step].x_dest - self.x_pos
        y_move = self.movements[self.step].y_dest - self.y_pos

        # normalise vector
        length: float = math.sqrt(math.pow(x_move, 2) + math.pow(y_move, 2))
        x_move = x_move / length
        y_move = y_move / length

        # multiply with speed
        x_move = x_move * self.movements[self.step].speed
        y_move = y_move * self.movements[self.step].speed

        return x_move, y_move


def filter_ns2(path: str, node_name: str) -> List[str]:
    """Reads in a ns2-movement-script and filters out all commands which are not for the specified node or commented"""
    node_id: str = node_name[1:]

    commands: List[str] = []
    with open(path, "r") as f:
        for line in f:
            if f"node_({node_id})" in line:
                # filter out commented commands
                if not line[0] == "#":
                    commands.append(line.strip())
    return commands


def parse_movement(rest_url: str, path: str, node_name: str) -> NS2Movements:
    """Turns the ns2 text file into a NS2Movement object"""
    commands = filter_ns2(path=path, node_name=node_name)
    start_x: float = 0.0
    start_y: float = 0.0
    movements: List[NS2Movement] = []

    for command in commands:
        split: List[str] = command.split(" ")
        if "X_" in split:
            start_x = float(split[3])
        elif "Y_" in split:
            start_y = float(split[3])
        elif "setdest" in split:
            timestamp = int(float(split[2]))
            x_dest = float(split[5])
            y_dest = float(split[6])
            speed = float(split[7][:-1])
            movements.append(
                NS2Movement(
                    timestamp=timestamp, x_dest=x_dest, y_dest=y_dest, speed=speed
                )
            )

    return NS2Movements(
        rest_url=rest_url,
        node_name=node_name,
        x_pos=start_x,
        y_pos=start_y,
        movements=movements,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates context data of node movement."
    )
    parser.add_argument("path", help="Path to the config file")
    args = parser.parse_args()

    node_config = toml.load(args.path)
    print(f"Using config: {node_config}", flush=True)

    nodes: Nodes = parse_scenario_xml(path=node_config["Scenario"]["xml"])
    this_node = nodes.get_node_for_name(node_name=node_config["Node"]["name"])
    print(f"This node's type: {this_node.type}", flush=True)

    if this_node.type != "visitor":
        print("This node type does not move", flush=True)
        sys.exit(0)

    if node_config["Experiment"]["routing"] != "context_complex":
        print("Experiment does not require context information", flush=True)
        sys.exit(0)

    routing_url = build_url(
        address=node_config["REST"]["address"], port=node_config["REST"]["routing_port"]
    )

    movement_context = parse_movement(
        rest_url=routing_url,
        path=node_config["Scenario"]["movements"],
        node_name=node_config["Node"]["name"],
    )

    movement_context.run()
