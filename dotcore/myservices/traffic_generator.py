import toml

from core.services import CoreService


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class TrafficGeneratorService(CoreService):
    name = "TrafficGenerator"
    executables = ("traffic_generator",)
    dependencies = ("dtn7",)
    configs = ("traffic_generator.toml",)
    startup = (
        'bash -c "nohup traffic_generator {} &> traffic_generator_run.log &"'.format(configs[0]),
    )

    @classmethod
    def generate_config(cls, node, filename):
        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = node.name
        config["Node"]["endpoint_id"] = "dtn://{}/".format(node.name)
        return toml.dumps(config)
