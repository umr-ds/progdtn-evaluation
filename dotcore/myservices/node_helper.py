import toml

from core.services import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class NodeHelperService(CoreService):
    name = "NodeHelper"
    executables = ("node_helper",)
    dependencies = ("dtn7",)
    configs = ("node_helper.toml",)
    startup = ('bash -c "nohup node_helper {} &> node_helper_run.log &"'.format(configs[0]), )

    @classmethod
    def generate_config(cls, node, filename):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        return toml.dumps(config)
