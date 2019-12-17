from core.services.coreservices import CoreService, ServiceMode


class BWMService(CoreService):
    name = "bwm-ng"
    group = "Logging"
    executables = ("bwm-ng",)
    validation_mode = ServiceMode.BLOCKING

    startup = (
        'bash -c "\
nohup bwm-ng --timeout=1000 --unit=bytes --type=rate --output=csv -F bwm.csv &> bwm.log & \
echo $! >> bwm.pid \
"',
    )

    shutdown = (
        'bash -c "\
kill `cat bwm.pid`; \
rm bwm.pid \
"',
    )

    @classmethod
    def generate_config(cls, node, filename):
        pass
