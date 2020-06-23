from core.nodes.base import CoreNode
from core.services.coreservices import CoreService

SCENARIO = "wanderwege"


class NodeHelperService(CoreService):

    name = "NodeHelper"
    executables = ("node_helper",)
    dependencies = ("dtn7",)
    configs = ("helper.toml",)
    startup = (f'bash -c "nohup node_helper {configs[0]} &> helpers_run.log &"',)

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        if filename == "helper.toml":
            return f"""
[Node]
name = "{node.name}"
endpoint_id = "dtn://{node.name}/"
store_log = "{node.nodedir}/store_log.csv"
log_file = "{node.nodedir}/helpers.log"
log_level = "INFO"

[REST]
address = "localhost"
agent_port = 8080
routing_port = 35043

[Scenario]
xml = "/dtn_routing/scenarios/{SCENARIO}/{SCENARIO}.xml"
movements = "/dtn_routing/scenarios/{SCENARIO}/{SCENARIO}.ns_movements"
wifi_range = 275.0
"""
