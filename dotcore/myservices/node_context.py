import toml

from core.nodes.base import CoreNode
from core.services.coreservices import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class TrafficGeneratorService(CoreService):
    name = "NodeContext"
    executables = ("node_context",)
    dependencies = ("dtn7",)
    configs = ("node_context.toml",)
    startup = (f'bash -c "nohup node_context {configs[0]} &> node_context_run.log &"',)

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        return toml.dumps(config)
