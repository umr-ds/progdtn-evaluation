import random

import xml.etree.ElementTree as ElementTree

from cadrhelpers.movement_generator import read_waypoints, transform_to_ns


def get_movement_file(xml_path: str) -> str:
    """Read the CORe XML-scenario file and extract the path to the ns2 movement file"""
    tree = ElementTree.parse(xml_path)
    root = tree.getroot()

    for child in root:
        if child.tag == "mobility_configurations":
            for mobility_config in child:
                if mobility_config.attrib["model"] == "ns2script":
                    for ns2_config in mobility_config:
                        if ns2_config.attrib["name"] == "file":
                            return ns2_config.attrib["value"]

    return ""


def generate_randomised_ns2(
    waypoint_file: str, core_xml: str, jitter: float, seed: int
) -> None:
    """Generate a randomised ns2 movement file

    Args:
        waypoint_file: Path to the csv-file containing the waypoints
        core_xml: Path to the core scenario xml file
        jitter: Maximum randomised wait time (set to negative value if you want no randomisation
        seed: Seed for Python's PRNG so you can get reproducible scenarios
    """
    random.seed(seed)
    ns2_path = get_movement_file(core_xml)
    waypoints = read_waypoints(waypoint_file=waypoint_file)
    transform_to_ns(waypoints=waypoints, output_file=ns2_path, jitter=jitter)
