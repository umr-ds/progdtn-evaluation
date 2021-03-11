import toml

from core.nodes.base import CoreNode
from core.services.coreservices import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class NodeHelperService(CoreService):
    name = "NodeHelper"
    executables = ("node_helper",)
    dependencies = ("dtn7",)
    configs = ("node_helper.toml",)
    startup = (f'bash -c "nohup node_helper {configs[0]} &> node_helper_run.log &"',)

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        return toml.dumps(config)
