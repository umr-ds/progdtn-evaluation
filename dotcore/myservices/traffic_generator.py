import toml

from core.services.coreservices import CoreService


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
        if node.name == "n2":
            name = "coordinator"
        else:
            name = node.name

        config = toml.load(EXPERIMENT_CONFIG)
        config["Node"] = {}
        config["Node"]["name"] = name
        config["Node"]["endpoint_id"] = "dtn://{}/".format(name)
        return toml.dumps(config)
