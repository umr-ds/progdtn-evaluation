from core.service import CoreService
from core.service import ServiceMode

class BWMService(CoreService):
    name = "bwm-ng"
    group = "Logging"
    executables = ('bwm-ng', )
    startup = ('bash -c "\
nohup bwm-ng --timeout=1000 --unit=bytes --type=rate --output=csv -F bwm.csv &> bwm.log & \
echo $! >> bwm.pid \
"', )
    shutdown = ('bash -c "\
kill `cat bwm.pid`; \
rm bwm.pid \
"', )
    validation_mode = ServiceMode.BLOCKING
