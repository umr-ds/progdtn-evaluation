import toml

from core.nodes.base import CoreNode
from core.services.coreservices import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class TrafficGeneratorService(CoreService):
    name = "TrafficGenerator"
    executables = ("traffic_generator",)
    dependencies = ("dtn7",)
    configs = ("traffic_generator.toml",)
    startup = (
        f'bash -c "nohup traffic_generator {configs[0]} &> traffic_generator_run.log &"',
    )

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        config["Node"]["endpoint_id"] = f"dtn://{node.name}/"
        return toml.dumps(config)
