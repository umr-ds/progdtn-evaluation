#! /usr/bin/env python3

from __future__ import annotations
from typing import Dict, Union, List
from json import loads
from glob import glob
import os
import json
from dataclasses import dataclass

@dataclass
class Scenario:
    bundles_per_node: int
    seed: int
    routing: str
    payload_size: int
    instance_id: int

    def __eq__(self, other) -> bool:
        return isinstance(other, Scenario) and self.instance_id == other.instance_id

    def __hash__(self) -> int:
        return self.instance_id.__hash__()

    def matches(self, other: Scenario) -> bool:
        return (
            self.bundles_per_node == other.bundles_per_node
            and self.seed == other.seed
            and self.payload_size == other.payload_size
            and self.instance_id != other.instance_id
        )


@dataclass
class TrafficGenerator:
    node_id: str
    rng_seed: str
    timestamps: List[int]
    wait_times: List[int]
    num_sent: int
    num_dtnd: int
    really_sent: int

    def __eq__(self, other):
        return isinstance(other, TrafficGenerator) and self.node_id == other.node_id

    def matches(self, other: TrafficGenerator) -> bool:
        return (
            self.rng_seed == other.rng_seed
            and self.timestamps == other.timestamps
            and self.wait_times == other.wait_times
        )

    def difference(self, other: TrafficGenerator) -> None:
        if self.rng_seed != other.rng_seed:
            print(f"Seeds: {self.rng_seed} : {other.rng_seed}")
        if self.timestamps != other.timestamps:
            print(f"Timestamps: {self.timestamps} : {other.timestamps}")
        if self.wait_times != other.wait_times:
            print(f"Wait Times: {self.wait_times} : {other.wait_times}")


def parse_instance_parameters(path: str) -> Scenario:
    params: Dict[str, Union[str, int]] = {}
    with open(path, "r") as f:
        # I don't know any better way to do this
        # I tried executing the code with exec() and then accessing the assigned variables
        # but that doesn't work. Probably because of some namespacing issue...
        # (I can see the variables with the correct values in the debugger, but I can't access them in code
        for line in f:
            if "params =" in line:
                pseudo_json = line.split("=")[1].strip().replace("'", '"')
                params = loads(pseudo_json)

    scenario = Scenario(
        bundles_per_node=params["bundles_per_node"],
        seed=params["seed"],
        routing=params["routing"],
        payload_size=params["payload_size"],
        instance_id=params["simInstanceId"],
    )

    return scenario


def parse_traffic_generator(path: str) -> TrafficGenerator:
    node_id = ""
    rng_seed = ""
    timestamps: List[int] = []
    wait_times: List[int] = []
    num_sent = 0
    num_dtnd = 0
    really_sent = 0
    
    with open(path, "r") as f:
        for line in f:
            if "Using config:" in line:
                pseudo_json = line[13:].strip().replace("'", '"')
                config = loads(pseudo_json)
                node_id = config["Node"]["name"]
            if "RNG seed:" in line:
                rng_seed = line[9:].strip()
            if "Timestamps for bundle generation:" in line:
                timestamps = loads(line[33:].strip())
            if "Wait times for these timestamps:" in line:
                wait_times = loads((line[32:].strip()))
            if "Sending bundle" in line:
                really_sent = really_sent + 1
        
    dtnd_path = f"{os.path.dirname(os.path.abspath(path))}/{node_id}.conf_dtnd_run.log"
    with open(dtnd_path, "r") as f:
        for line in f:
            if "REST client sent bundle" in line:
                num_dtnd = num_dtnd + 1
                
    
    return TrafficGenerator(
        node_id=node_id, rng_seed=rng_seed, timestamps=timestamps, wait_times=wait_times, num_sent=len(timestamps), num_dtnd=num_dtnd, really_sent=really_sent
    )

if __name__ == '__main__':
    EXPERIMENT_PATH = "/research_data/debug/ids/"
    scenarios: List[Scenario] = []
    instances: Dict[Scenario, List[TrafficGenerator]] = {}

    instance_paths: List[str] = glob(os.path.join(EXPERIMENT_PATH, "*"))
    for instance_path in instance_paths:
        scenario = parse_instance_parameters(os.path.join(instance_path, "parameters.py"))
        scenarios.append(scenario)

        node_paths = glob(path.join(instance_path, "*.conf_traffic_generator_run.log"))
        generators: List[TrafficGenerator] = []
        for node_path in node_paths:
            node_generator = parse_traffic_generator(node_path)
            generators.append(node_generator)

        instances[scenario] = generators

    for scenario in scenarios:
        for other_scenario in scenarios:
            if scenario.matches(other_scenario):
                generators_a = instances[scenario]
                generators_b = instances[other_scenario]

                for generator in generators_a:
                    for other_generator in generators_b:
                        if generator == other_generator:
                            if not generator.matches(other_generator):
                                foo = generator.matches(other_generator)
                                print(
                                    f"Mismatch between instances {scenario.instance_id} and {other_scenario.instance_id}:"
                                )
                                print(
                                    f"Params: bundles_per_node: {scenario.bundles_per_node}, seed: {scenario.seed}, payload_size: {scenario.payload_size}"
                                )
                                print(f"Node: {generator.node_id}")
                                print("Differences:")
                                generator.difference(other_generator)
                                print("-----------------------------")
                            else:
                                print(f"Instances {scenario.instance_id} and {other_scenario.instance_id} match.")
