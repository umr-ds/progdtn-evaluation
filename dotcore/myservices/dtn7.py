import toml

from core.services.coreservices import CoreService, ServiceMode

from cadrhelpers.util import parse_scenario_xml, get_node_type


EXPERIMENT_CONFIG = "/dtn_routing/experiment_config.toml"


class Dtn7Service(CoreService):
    name = "dtn7"
    group = "dtn"
    executables = ("dtnd", "dtn-tool")
    dependencies = ("bwm-ng", "pidstat")
    configs = ("dtnd.toml", "context.js")
    startup = ('bash -c "nohup dtnd {} &> dtnd_run.log &"'.format(configs[0]), )
    validation_timer = 1  # Wait 1 second before validating service.
    validation_period = 1  # Retry after 1 second if validation was not successful.
    validation_mode = ServiceMode.NON_BLOCKING # NON_BLOCKING uses the validate commands for validation.
    shutdown = ('bash -c "kill -INT `pgrep dtnd`"', )
    validate = (
        'bash -c "ps -C dtnd"',
    )  # ps -C returns 0 if the process is found, 1 if not.

    @classmethod
    def generate_config(cls, node, filename):
        experiment_config = toml.load(EXPERIMENT_CONFIG)

        nodes = parse_scenario_xml(experiment_config["Scenario"]["xml"])
        node_type = get_node_type(nodes=nodes, name=node.name)

        if node_type == "coordinator":
            cla_id = '"dtn://coordinator/"'
        else:
            cla_id = '"dtn://{}/"'.format(node.name)

        routing = experiment_config["Experiment"]["routing"]

        if filename == "dtnd.toml":
            # if we are running "context_epidemic" or "context_complex",
            # the second part signifies the specific script that the routing algorithm should be instantiated with
            if "context" in routing:
                routing = "context"

            agent_address = "localhost:{}".format(experiment_config['REST']['agent_port'])
            routing_address = "localhost:{}".format(experiment_config['REST']['routing_port'])

            return """
[core]
store = "store_{nodename}"
node-id = {cla_id}
inspect-all-bundles = true

[logging]
level = "debug"
report-caller = false
format = "json"

[discovery]
ipv4 = true
ipv6 = false
interval = 2

[agents]
[agents.webserver]
address = "{agent_address}"
websocket = true
rest = true

[[listen]]
protocol = "mtcp"
endpoint = ":4556"

[routing]
algorithm = "{routing}"

# config for spray routing
[routing.sprayconf]
multiplicity = 5

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
scriptpath = "{nodedir}/context.js"
listenaddress = "{routing_address}"

""".format(nodename=node.name, cla_id=cla_id, agent_address=agent_address, routing=routing, nodedir=node.nodedir, routing_address=routing_address)

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
