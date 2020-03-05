from core.nodes.base import CoreNode
from core.services.coreservices import CoreService


class SensorHelperService(CoreService):

    name = "SensorHelper"
    executables = ("helper_sensor",)
    dependencies = ("DTN7",)
    configs = ("sensor.toml",)
    startup = (f'bash -c "nohup helper_sensor {configs[0]}"',)

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        if filename == "sensor.toml":
            return f"""
[Node]
name = "{node.name}"
store_log = "{node.nodedir}/store_log.csv"
log_file = "{node.nodedir}/helpers.log"
log_level = "DEBUG"

[REST]
address = "127.0.0.1"
bundle_port = 35038
context_port = 35043

[Scenario]
xml = "/dtn-routing/scenarios/wanderwege/wanderwege.xml"
movements = "/dtn-routing/scenarios/randomWaypoint/randomWaypoint.ns_movements"
wifi_range = 275.0
"""
