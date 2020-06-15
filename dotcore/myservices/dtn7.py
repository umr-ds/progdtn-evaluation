import os

from core.nodes.base import CoreNode
from core.services.coreservices import CoreService, ServiceMode

from cadrhelpers.movement_context import parse_scenario_xml, get_node_type


XML_PATH = "/dtn_routing/scenarios/wanderwege/wanderwege.xml"


class Dtn7Service(CoreService):
    name = "dtn7"
    group = "dtn"
    executables = ("dtnd", "dtn-tool")
    dependencies = ()
    configs = ("dtnd.toml", "context.js")
    startup = (f'bash -c "nohup dtnd {configs[0]} &> dtnd_run.log &"',)
    validation_timer = 1  # Wait 1 second before validating service.
    validation_period = 1  # Retry after 1 second if validation was not successful.
    validation_mode = (
        ServiceMode.NON_BLOCKING
    )  # NON_BLOCKING uses the validate commands for validation.
    shutdown = ('bash -c "kill -INT `pgrep dtnd`"',)
    validate = (
        'bash -c "ps -C dtnd"',
    )  # ps -C returns 0 if the process is found, 1 if not.

    @classmethod
    def generate_config(cls, node: CoreNode, filename: str):
        if os.path.isfile("/tmp/routing"):
            with open("/tmp/routing", "r") as f:
                routing = f.read().strip()
        else:
            routing = "epidemic"

        nodes = parse_scenario_xml(XML_PATH)
        node_type = get_node_type(nodes=nodes, name=node.name)

        if node_type == "backbone":
            cla_id = 'node = "dtn://backbone/"'
        else:
            cla_id = ""

        if filename == "dtnd.toml":
            # if we are running "context_epidemic" or "context_complex",
            # the second part signifies the specific script that the routing algorithm should be instantiated with
            if "context" in routing:
                routing = "context"

            return f"""
[core]
store = "store_{node.name}"
node-id = "dtn://{node.name}/"
inspect-all-bundles = true

[logging]
level = "debug"
report-caller = false
format = "json"

[discovery]
ipv4 = true
ipv6 = true
interval = 30

[agents]
[agents.webserver]
address = "localhost:8080"
websocket = true
rest = true

[[listen]]
protocol = "tcpcl"
endpoint = ":4556"
{cla_id}

[routing]
algorithm = "{routing}"

# config for spray routing
[routing.sprayconf]
multiplicity = 10

# config for dtlsr
[routing.dtlsrconf]
recomputetime = "30s"
broadcasttime = "30s"
purgetime = "10m"

# config for prophet
[routing.prophetconf]
# pinit ist the prophet initialisation constant (default value provided by the PROPHET-paper)
pinit = 0.75
# beta is the prophet scaling factor for transitive predictability (default value provided by the PROPHET-paper)
beta = 0.25
# gamma is the prophet ageing factor (default value provided by the PROPHET-paper)
gamma = 0.98
ageinterval = "1m"

[routing.contextconf]
scriptpath = "{node.nodedir}/context.js"
listenaddress = "127.0.0.1:35043"

"""

        elif filename == "context.js":
            if "epidemic" in routing:
                with open("/root/context_epidemic.js", "r") as f:
                    context = f.read()
                    return context
            elif "complex" in routing:
                with open("/root/context_complex.js", "r") as f:
                    context = f.read()
                    return context
            elif "spray" in routing:
                with open("/root/context_spray.js", "r") as f:
                    context = f.read()
                    return context
            else:
                return ""

        else:
            return ""
