from core.nodes.base import CoreNode
from core.services.coreservices import CoreService


class NodeHelperService(CoreService):

    name = "NodeHelper"
    executables = ("node_helper",)
    dependencies = ("DTN7",)
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
address = "127.0.0.1"
bundle_port = 35038
context_port = 35043

[Scenario]
xml = "/dtn_routing/scenarios/wanderwege/wanderwege.xml"
movements = "/dtn_routing/scenarios/randomWaypoint/randomWaypoint.ns_movements"
wifi_range = 275.0
"""
