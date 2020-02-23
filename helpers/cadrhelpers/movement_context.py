import multiprocessing
import time
import math

from cadrhelpers.dtnclient import send_context, build_url
from typing import List, Tuple, Dict


class NS2Movement:
    """A node's movements as specified in a ns2 movement script

    Attributes:
        node_name: Self explanatory
        rest_url: URL of the context-REST-interface
        step: Current position in the list of movements
        position: Current position in the form (x_pos, y_pos)
        movements: List of movement commands in the form (timestamp, dest_x_pos, dest_y_pos, speed)
    """

    def __init__(
        self,
        rest_url: str,
        node_name: str,
        start_position: Tuple[float, float],
        movements: List[Tuple[int, float, float, float]],
    ):
        self.node_name: str = node_name
        self.rest_url: str = rest_url
        self.position: Tuple[float, float] = start_position
        self.movements: List[Tuple[int, float, float, float]] = movements
        self.step: int = 0

    def run(self) -> None:
        """Performs periodic context updates when movement changes
        Spawns a new process
        """
        process = multiprocessing.Process(target=self._run)
        process.start()

    def _run(self) -> None:
        """Does the actual work"""
        # differentiate between node who start moving immediately and those who take a while to get going
        if self.movements[0][0] != 0:
            time.sleep(self.movements[0][0])

        vector = self.compute_vector()
        self.update_context(vector)
        self.move_step()

        # main wait-and-update-loop
        while self.step < len(self.movements):
            wait_time: int = self.movements[self.step][0] - self.movements[
                self.step - 1
            ][0]
            time.sleep(wait_time)
            vector = self.compute_vector()
            self.update_context(vector)
            self.move_step()

    def move_step(self) -> None:
        """Update the node's internal position and step counter"""
        self.position = (self.movements[self.step][1], self.movements[self.step][2])
        self.step += 1

    def update_context(self, vector: Tuple[float, float]) -> None:
        """Update node context in dtnd"""
        context: Dict[str, float] = {"x": vector[0], "y": vector[1]}
        send_context(
            rest_url=self.rest_url, context_name="movement", node_context=context
        )

    def compute_vector(self) -> Tuple[float, float]:
        """Take the node's current position and destination/speed and compute the movement vector"""
        x_move = self.movements[self.step][1] - self.position[0]
        y_move = self.movements[self.step][2] - self.position[1]

        # normalise vector
        length: float = math.sqrt(math.pow(x_move, 2) + math.pow(y_move, 2))
        x_move = x_move / length
        y_move = y_move / length

        # multiply with speed
        x_move = x_move * self.movements[self.step][3]
        y_move = y_move * self.movements[self.step][3]

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


def generate_movement(rest_url: str, path: str, node_name: str) -> NS2Movement:
    """Turns the ns2 text file into a NS2Movement object"""
    commands = filter_ns2(path=path, node_name=node_name)
    start_position: Tuple[float, float] = (0.0, 0.0)
    movements: List[Tuple[int, float, float, float]] = []

    for command in commands:
        split: List[str] = command.split(" ")
        if "X_" in split:
            start_position = (float(split[3]), start_position[1])
        elif "Y_" in split:
            start_position = (start_position[0], float(split[3]))
        elif "setdest" in split:
            timestamp = int(float(split[2]))
            x_dest = float(split[5])
            y_dest = float(split[6])
            speed = float(split[7][:-1])
            movements.append((timestamp, x_dest, y_dest, speed))

    return NS2Movement(
        rest_url=rest_url,
        node_name=node_name,
        start_position=start_position,
        movements=movements,
    )


if __name__ == "__main__":
    url = build_url(address="localhost", port=35043)
    ns2_movement = generate_movement(
        rest_url=url,
        path="/home/msommer/devel/cadr-evaluation/scenarios/randomWaypoint/randomWaypoint.ns_movements",
        node_name="n11",
    )
    ns2_movement._run()
