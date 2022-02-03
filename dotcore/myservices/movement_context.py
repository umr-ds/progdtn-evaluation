import toml

from core.services import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class TrafficGeneratorService(CoreService):
    name = "MovementContext"
    executables = ("movement_context",)
    dependencies = ("dtn7",)
    configs = ("movement_context.toml",)
    startup = (
        f'bash -c "nohup movement_context {configs[0]} &> movement_context_run.log &"',
    )

    @classmethod
    def generate_config(cls, node, filename):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        return toml.dumps(config)
