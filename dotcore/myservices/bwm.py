from core.services import CoreService, ServiceMode


class BWMService(CoreService):
    name = "bwm-ng"
    group = "Logging"
    executables = ("bwm-ng",)

    validation_mode = ServiceMode.BLOCKING
    validate = ('bash -c "ps -C bwm-ng"', )     # ps -C returns 0 if the process is found, 1 if not.
    validation_timer = 1                        # Wait 1 second before validating service.
    validation_period = 1                       # Retry after 1 second if validation was not successful.

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
