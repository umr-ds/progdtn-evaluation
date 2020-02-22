from typing import List, Tuple


class NS2Movement:
    def __init__(
            self,
            node_name: str,
            start_position: Tuple[float, float],
            movements: List[Tuple[float, float, float]]
    ):
        self.start_position = start_position
        self.movements = movements
        self.node_name = node_name


def filter_ns2(path: str, node_name: str) -> List[str]:
    """Reads in a ns2-movement-script and filters out all commands which are not for the specified node or commented out

    Args:
        path (str): Path to the movement-script
        node_name (str): name of the node

    Returns:
        List[str]: Filtered list of commands
    """
    node_id: str = node_name[1:]

    commands: List[str] = []
    with open(path, "r") as f:
        for line in f:
            if f"node_({node_id})" in line:
                # filter out commented commands
                if not line[0] == "#":
                    commands.append(line.strip())
    return commands


def parse_ns2(path: str, node_name: str) -> NS2Movement:
    commands = filter_ns2(path=path, node_name=node_name)
    start_position: Tuple[float, float] = (0.0, 0.0)
    movements: List[Tuple[float, float, float]] = []

    for command in commands:
        split: List[str] = command.split(" ")
        if "X_" in split:
            start_position = (float(split[3]), start_position[1])
        elif "Y_" in split:
            start_position = (start_position[0], float(split[3]))
        elif "setdest" in split:
            x_dest = float(split[5])
            y_dest = float(split[6])
            speed = float(split[7][:-1])
            movements.append((x_dest, y_dest, speed))

    return NS2Movement(node_name=node_name, start_position=start_position, movements=movements)


if __name__ == "__main__":
    ns2_movement = parse_ns2(
        path="/home/msommer/devel/cadr-evaluation/scenarios/randomWaypoint/randomWaypoint.ns_movements",
        node_name="n2"
    )
