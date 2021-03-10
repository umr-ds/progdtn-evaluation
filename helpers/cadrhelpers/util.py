import math
from typing import Tuple

from cadrhelpers.movement_context import Node


def is_context(name: str) -> Tuple[bool, str]:
    context = "context" in name

    context_algorithm = ""
    if context:
        context_algorithm: str = routing.split("_")[1]

    return context, context_algorithm


def compute_euclidean_distance(node_a: Node, node_b: Node) -> float:
    x_diff = math.pow(node_a.x_pos - node_b.x_pos, 2)
    y_diff = math.pow(node_a.y_pos - node_b.y_pos, 2)
    return math.sqrt(x_diff + y_diff)