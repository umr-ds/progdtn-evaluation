from core.services.coreservices import CoreService, ServiceMode


class Dtn7Service(CoreService):
    name = "DTN7"

    group = "DTN"

    executables = ("dtn7d", "dtn7cat", )

    dependencies = ("bwm-ng", "pidstat")

    configs = ("dtn7d.toml", )

    startup = (f'bash -c "nohup dtn7d {configs[0]} &> dtn7d_run.log &"', )

    validate = ('bash -c "ps -C dtn7d"', )      # ps -C returns 0 if the process is found, 1 if not.

    validation_mode = ServiceMode.NON_BLOCKING  # NON_BLOCKING uses the validate commands for validation.

    validation_timer = 1                        # Wait 1 second before validating service.

    validation_period = 1                       # Retry after 1 second if validation was not successful.

    shutdown = ('bash -c "kill -INT `pgrep dtn7d`"', )

    @classmethod
    def generate_config(cls, node, filename):
        return f'''
[core]
store = "store_{node.name}"
node-id = "dtn://{node.name}/"

[logging]
level = "debug"
report-caller = false
format = "text"

[discovery]
ipv4 = true
interval = 2

[simple-rest]
node = "dtn://{node.name}/"
listen = "127.0.0.1:8080"

[[listen]]
protocol = "mtcp"
endpoint = ":35037"

[routing]
algorithm = "prophet"

[routing.sprayconf]
multiplicity = 10

[routing.dtlsrconf]
recomputetime = "30s"
broadcasttime = "30s"
purgetime = "10m"

[routing.prophetconf]
pinit = 0.75
beta = 0.25
gamma = 0.98
ageinterval = "30s"
        '''
