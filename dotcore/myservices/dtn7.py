from core.services.coreservices import CoreService, ServiceMode


class Dtn7Service(CoreService):
    name = "DTN7"
    group = "DTN"
    executables = ("dtn7d", "dtn7cat", "dtnclient")
    dependencies = ("bwm-ng", "pidstat")
    configs = ("dtn7d.toml", "context.js")
    startup = (f'bash -c "nohup dtn7d {configs[0]} &> dtn7d_run.log &"',)
    validation_timer = 1  # Wait 1 second before validating service.
    validation_period = 1  # Retry after 1 second if validation was not successful.
    validation_mode = ServiceMode.NON_BLOCKING  # NON_BLOCKING uses the validate commands for validation.
    shutdown = ('bash -c "kill -INT `pgrep dtn7d`"',)
    validate = (
        'bash -c "ps -C dtn7d"',
    )  # ps -C returns 0 if the process is found, 1 if not.

    @classmethod
    def generate_config(cls, node, filename):
        if filename == "dtn7d.toml":
            return f"""
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

[context-rest]
listen = "127.0.0.1:35038"

[[listen]]
protocol = "mtcp"
endpoint = ":35037"

[routing]
algorithm = "context"

[routing.contextconf]
scriptpath = "{node.nodedir}/context.js"
listenaddress = "127.0.0.1:35043"
"""
        elif filename == "context.js":
            with open("/root/context.js", "r") as f:
                context = f.read()
                return context
        else:
            return ""
