#! /usr/bin/env python3

import argparse
import math
import csv
import random

from typing import List, Dict
from dataclasses import dataclass


# selection of different methods of locomotion, with speeds (in m/s)
# and reasonable derivations to add a bit of randomness
LOCOMOTION = {
    "walk": {"low": 1.25, "high": 1.5},
    "powerwalk": {"low": 1.9, "high": 2.5},
    "jog": {"low": 3.0, "high": 3.6},
}
# define the fastest method of locomotion
LOCOMOTION["fastest"] = LOCOMOTION["jog"]


@dataclass()
class Point:
    node: str
    x: float
    y: float


def read_waypoints(waypoint_file: str) -> Dict[str, List[Point]]:
    with open(waypoint_file, "r") as f:
        reader = csv.reader(f)
        movement_points: Dict[str, List[Point]] = {}
        for row in reader:
            point = Point(row[0], float(row[1]), float(row[2]))
            if row[0] in movement_points:
                movement_points[row[0]].append(point)
            else:
                movement_points[row[0]] = [point]
        return movement_points


def compute_travel_time(
    distance: float,
    speed: float,
    wait_time: float = 2.0,
    jitter: float = -1.0,
    precision: int = 2,
) -> float:
    """Compute the time needed to travel the given distance.
    Includes an optional grace period to compensate for numerical error during floating point computations.
    """
    if jitter > 0:
        random_wait: float = random.uniform(0, jitter)
    else:
        random_wait = 0.0

    return round((distance / speed) + wait_time + random_wait, precision)


def compute_distance(
    start_x: float, start_y: float, end_x: float, end_y: float, precision: int = 2
) -> float:
    x_dist: float = end_x - start_x
    y_dist: float = end_y - start_y
    distance = math.sqrt((x_dist * x_dist) + (y_dist * y_dist))
    return round(distance, precision)


def node_speed(
    locomotion: str,
    fast_mode: bool = False,
    ludicrous_speed: bool = False,
    precision: int = 2,
) -> float:
    if fast_mode:
        speed = LOCOMOTION["fastest"]["high"]
    else:
        speed = random.uniform(
            LOCOMOTION[locomotion]["low"], LOCOMOTION[locomotion]["high"]
        )

    if ludicrous_speed:
        speed *= 10

    return round(speed, precision)


def transform_to_ns(
    waypoints: Dict[str, List[Point]],
    output_file: str,
    wait_time: float = 2.0,
    jitter: float = -1.0,
    fast_mode: bool = False,
    ludicrous_speed: bool = False,
) -> None:
    with open(output_file, "w") as f:
        f.write(f"# nodes: {len(waypoints.keys())}\n")
        for node in waypoints.keys():
            f.write("\n")
            node_movements = waypoints[node]
            current_point = node_movements[0]
            f.write(f"$node_({node}) set X_ {current_point.x}\n")
            f.write(f"$node_({node}) set Y_ {current_point.y}\n")

            node_locomotion: str = random.choice(list(LOCOMOTION))

            current_time: float = 1.0
            for next_point in node_movements[1:]:
                speed = node_speed(
                    locomotion=node_locomotion,
                    fast_mode=fast_mode,
                    ludicrous_speed=ludicrous_speed,
                )
                f.write(
                    f'$ns_ at {current_time} "$node_({node}) setdest {next_point.x} {next_point.y} {speed}"\n'
                )
                distance = compute_distance(
                    start_x=current_point.x,
                    start_y=current_point.y,
                    end_x=next_point.x,
                    end_y=next_point.y,
                )
                current_time += compute_travel_time(
                    distance=distance, speed=speed, wait_time=wait_time, jitter=jitter
                )
                current_time = round(current_time, 0)
                current_point = next_point

            print(f"Course-completion time for n{node}:")
            print(f"{current_time}s")
            print(f"{round(current_time/60, 2)}min")
            print(f"{round(current_time/3600, 2)}h")
            print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Takes a position-file and generate a ns-2 movement file"
    )
    parser.add_argument("input", help="path to the waypoint file")
    parser.add_argument("output", help="path for resulting ns2-file")
    parser.add_argument(
        "--ludicrous_speed",
        action="store_true",
        help="make everyone move with 10 times their normal speed",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        default="Have all nodes run with the maximum speed, so that you can make sure that you trace takes long enough",
    )
    parser.add_argument(
        "-w",
        "--wait_time",
        type=float,
        default=2.0,
        help="set wait time between arriving at one waypoint and departing for the next",
    )
    parser.add_argument(
        "-j",
        "--jitter",
        type=float,
        default=-1.0,
        help="Set to value >0 to have nodes wait for a random time period at waipoints",
    )
    parser.add_argument(
        "--seed",
        help="optional seed for the software RNG, set to get a deterministic result",
    )
    args = parser.parse_args()

    waypoints = read_waypoints(args.input)

    if args.seed:
        random.seed(args.seed)

    transform_to_ns(
        waypoints=waypoints,
        output_file=args.output,
        wait_time=args.wait_time,
        jitter=args.jitter,
        fast_mode=args.fast,
        ludicrous_speed=args.ludicrous_speed,
    )
