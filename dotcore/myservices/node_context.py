import toml

from core.services.coreservices import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class TrafficGeneratorService(CoreService):
    name = "NodeContext"
    executables = ("node_context",)
    dependencies = ("dtn7",)
    configs = ("node_context.toml",)
    startup = ('bash -c "nohup node_context {} &> node_context_run.log &"'.format(configs[0]), )

    @classmethod
    def generate_config(cls, node, filename):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        return toml.dumps(config)
