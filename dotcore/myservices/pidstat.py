from core.services.coreservices import CoreService, ServiceMode


class PidstatService(CoreService):
    name = "pidstat"
    group = "Logging"
    executables = ("pidstat",)

    validation_mode = ServiceMode.BLOCKING
    validation_timer = 1                        # Wait 1 second before validating service.
    validation_period = 1                       # Retry after 1 second if validation was not successful.

    startup = (
        'bash -c " \
nohup pidstat -drush -p ALL 1 > pidstat 2> pidstat.log & \
echo $! > pidstat.pid \
"',
    )
    shutdown = (
        'bash -c " \
kill `cat pidstat.pid`; \
rm pidstat.pid \
"',
    )

    @classmethod
    def generate_config(cls, node, filename):
        pass
