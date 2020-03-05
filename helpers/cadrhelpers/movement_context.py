import multiprocessing
import time
import math
import logging

import xml.etree.ElementTree as ElementTree

from cadrhelpers.dtnclient import send_context, build_url
from typing import List, Tuple, Dict, Union
from dataclasses import dataclass


@dataclass()
class NS2Movement:
    """Single movement command"""

    timestamp: int
    x_dest: float
    y_dest: float
    speed: float


@dataclass()
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

    node_name: str
    rest_url: str
    x_pos: float
    y_pos: float
    movements: List[NS2Movement]
    step: int = 0
    logger: logging.Logger = logging.getLogger(__name__)

    def run(self) -> None:
        """Performs periodic context updates when movement changes
        Spawns a new process
        """
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self) -> None:
        """Does the actual work"""
        # differentiate between node who start moving immediately and those who take a while to get going
        if self.movements[0].timestamp != 0:
            self.logger.debug(
                f"No inital movement, waiting for {self.movements[0].timestamp} seconds"
            )
            time.sleep(self.movements[0].timestamp)

        vector = self.compute_vector()
        self.logger.debug(f"New movement vector: {vector}")
        self.update_context(vector)
        self.move_step()
        self.logger.debug(f"Position at end of movement: ({self.x_pos}, {self.y_pos})")

        # main wait-and-update-loop
        while self.step < len(self.movements):
            wait_time: int = self.movements[self.step].timestamp - self.movements[
                self.step - 1
            ].timestamp
            self.logger.debug(f"Next change in movement in {wait_time} seconds")
            time.sleep(wait_time)
            vector = self.compute_vector()
            self.logger.debug(f"New movement vector: {vector}")
            self.update_context(vector)
            self.move_step()
            self.logger.debug(
                f"Position at end of movement: ({self.x_pos}, {self.y_pos})"
            )

    def move_step(self) -> None:
        """Update the node's internal position and step counter"""
        self.x_pos = self.movements[self.step].x_dest
        self.y_pos = self.movements[self.step].y_dest
        self.step += 1

    def update_context(self, vector: Tuple[float, float]) -> None:
        """Update node context in dtnd"""
        context: Dict[str, float] = {"x": vector[0], "y": vector[1]}
        self.logger.debug(f"Sending movement vector to dtnd: {context}")
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


def generate_movement(rest_url: str, path: str, node_name: str) -> NS2Movements:
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


@dataclass()
class Node:
    """Simulation node"""

    id: int
    name: str
    type: str
    x_pos: float
    y_pos: float


@dataclass()
class Nodes:
    """All the nodes in the simulation"""

    visitors: List[Node]
    sensors: List[Node]
    backbone: List[Node]

    def get_node_for_name(self, node_name: str) -> Node:
        ourself: Union[Node, None] = None

        for node in self.visitors + self.sensors + self.backbone:
            if node.name == node_name:
                ourself = node

        assert (
            ourself is not None
        ), "This node should really show up in the list of nodes"
        return ourself


def parse_scenario_xml(path: str) -> Nodes:
    """Parse the scenario's xml definition and separate the different types of nodes

    Returns:
        Three lists (visitors, sensors, backbone)
    """
    tree = ElementTree.parse(path)
    root = tree.getroot()

    visitors: List[Node] = []
    sensors: List[Node] = []
    backbone: List[Node] = []

    for child in root:
        if child.tag == "devices":
            for node_data in child:
                node = get_node_info(node_data)
                if node.type == "visitor":
                    visitors.append(node)
                elif node.type == "sensor":
                    sensors.append(node)
                elif node.type == "backbone":
                    backbone.append(node)

    return Nodes(visitors=visitors, sensors=sensors, backbone=backbone)


def get_node_info(element: ElementTree.Element) -> Node:
    """Extract the info aof a node from the xml tree"""
    node_id: int = int(element.attrib["id"])
    node_name: str = element.attrib["name"]
    node_type: str = element.attrib["type"]
    x_pos: float = 0.0
    y_pos: float = 0.0

    for sub_element in element:
        if sub_element.tag == "position":
            x_pos = float(sub_element.attrib["x"])
            y_pos = float(sub_element.attrib["y"])

    return Node(id=node_id, name=node_name, type=node_type, x_pos=x_pos, y_pos=y_pos)


if __name__ == "__main__":
    url = build_url(address="localhost", port=35043)
    ns2_movement = generate_movement(
        rest_url=url,
        path="/home/msommer/devel/cadr-evaluation/scenarios/randomWaypoint/randomWaypoint.ns_movements",
        node_name="n11",
    )

    nodes = parse_scenario_xml(
        "/home/msommer/devel/cadr-evaluation/scenarios/wanderwege/wanderwege.xml"
    )
